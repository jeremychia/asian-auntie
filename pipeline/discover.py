"""
Recipe URL discovery.

Two strategies:

1. category  — crawl paginated category listing pages and collect recipe links.
               Works for WordPress blogs with /page/N/ pagination.
               Assigns cuisine from the category URL used to find the link.

2. sitemap   — fetch the XML sitemap index, walk sub-sitemaps, and collect all
               post URLs. Faster and more complete, but doesn't carry cuisine
               information on its own (pair with a URL pattern map).
"""

import re
import sys
import html.parser
import urllib.parse
import xml.etree.ElementTree as ET
from typing import Optional

from pipeline.fetch import fetch

_SKIP_RE = re.compile(
    r"/(category|categories|tag|tags|page|author|search|wp-content|wp-admin"
    r"|feed|sitemap|about|contact|privacy|terms|shop|cart|checkout"
    r"|account|login|register|newsletter|subscribe|index|recipe-index"
    r"|collections|courses|ingredients)/",
    re.IGNORECASE,
)

_MEDIA_RE = re.compile(r"\.(jpg|jpeg|png|gif|pdf|mp4|webp|svg)($|\?)", re.IGNORECASE)


class _LinkExtractor(html.parser.HTMLParser):
    def __init__(self, base_url: str):
        super().__init__()
        self.base_url = base_url
        self.links: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href", "")
            if href and not href.startswith(("#", "mailto:", "tel:")):
                self.links.append(urllib.parse.urljoin(self.base_url, href))


def _is_recipe_link(url: str, base_domain: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    if parsed.netloc and parsed.netloc != base_domain:
        return False
    if _SKIP_RE.search(parsed.path):
        return False
    if _MEDIA_RE.search(parsed.path):
        return False
    path = parsed.path.strip("/")
    if not path or path.count("/") > 1:
        return False
    return True


def _normalise_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    return urllib.parse.urlunparse(parsed._replace(query="", fragment="")).rstrip("/")


def _paginate(base_url: str, page: int) -> str:
    if page == 1:
        return base_url
    return f"{base_url.rstrip('/')}/page/{page}/"


def discover_via_categories(
    categories: list[tuple[str, str]],
    max_pages: int,
    delay: float,
) -> list[tuple[str, str]]:
    """Crawl paginated category pages and return (url, cuisine) pairs.

    Each category tuple is (category_url, cuisine_label).
    Stops paginating when no new links appear on a page.
    """
    found: dict[str, str] = {}

    for category_url, cuisine in categories:
        base_domain = urllib.parse.urlparse(category_url).netloc
        print(
            f"  [discover] category={cuisine} — {category_url}",
            file=sys.stderr,
        )

        for page_num in range(1, max_pages + 1):
            page_url = _paginate(category_url, page_num)
            html_text = fetch(page_url, delay=delay)
            if not html_text:
                break

            extractor = _LinkExtractor(page_url)
            try:
                extractor.feed(html_text)
            except html.parser.HTMLParseError:
                pass

            page_links = [
                _normalise_url(urllib.parse.urljoin(page_url, link))
                for link in extractor.links
                if _is_recipe_link(urllib.parse.urljoin(page_url, link), base_domain)
            ]

            new = [u for u in page_links if u not in found]
            if not new:
                break
            for url in new:
                found[url] = cuisine
            print(
                f"    page {page_num}: {len(new)} new links ({len(found)} total)",
                file=sys.stderr,
            )

    return sorted(found.items())


def discover_via_sitemap(
    sitemap_index_url: str,
    url_filter: Optional[re.Pattern] = None,
    delay: float = 2.0,
) -> list[str]:
    """Walk an XML sitemap index and return all leaf page URLs.

    url_filter: if provided, only URLs matching this pattern are kept.
    Returns a sorted list of URLs (no cuisine information).
    """
    NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    found: set[str] = set()

    print(f"  [discover] sitemap index — {sitemap_index_url}", file=sys.stderr)
    index_xml = fetch(sitemap_index_url, delay=delay)
    if not index_xml:
        return []

    try:
        root = ET.fromstring(index_xml)
    except ET.ParseError as e:
        print(f"  [sitemap parse error] {e}", file=sys.stderr)
        return []

    sub_urls = [loc.text.strip() for loc in root.findall(".//sm:loc", NS) if loc.text]
    print(f"  [discover] {len(sub_urls)} sub-sitemaps found", file=sys.stderr)

    for sub_url in sub_urls:
        sub_xml = fetch(sub_url, delay=delay)
        if not sub_xml:
            continue
        try:
            sub_root = ET.fromstring(sub_xml)
        except ET.ParseError:
            continue
        for loc in sub_root.findall(".//sm:loc", NS):
            if loc.text:
                url = loc.text.strip()
                if url_filter is None or url_filter.search(url):
                    found.add(url)

    return sorted(found)
