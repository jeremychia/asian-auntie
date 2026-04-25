#!/usr/bin/env python3
"""
Recipe extraction pipeline CLI.

Workflow
--------
1. Scrape (results land in pipeline/staging/<site>.py for review)
   uv run python pipeline/run.py --site rasa_malaysia

2. Review pipeline/staging/rasa_malaysia.py — remove bad entries

3. Append approved entries to app/recipes/data.py
   (copy the dict blocks directly — format is identical)

4. Optionally regenerate data.py from all approved caches:
   uv run python pipeline/run.py --from-cache --output app/recipes/data.py

Other commands
--------------
# Discover URLs only (no recipe pages fetched — good first sanity check)
uv run python pipeline/run.py --site rasa_malaysia --discover-only

# Scrape up to N new recipes (skips already-cached URLs)
uv run python pipeline/run.py --site rasa_malaysia --limit 10

# Force re-scrape everything (ignores cache)
uv run python pipeline/run.py --site rasa_malaysia --no-cache

# List configured sites
uv run python pipeline/run.py --list-sites
"""

import sys
import pathlib
import argparse

# Allow running as a script from project root without installing the package.
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from pipeline.sites import SITES
from pipeline.fetch import fetch
from pipeline.discover import discover_via_categories, discover_via_sitemap
from pipeline.extract import find_recipe_jsonld, map_to_recipe
from pipeline import store


def _scrape_site(
    site_key: str,
    site: dict,
    limit: int | None,
    no_cache: bool,
    write_staging: bool = True,
) -> int:
    """Scrape one site and append new recipes to its cache. Returns count of new recipes."""
    if no_cache:
        store.clear_cache(site_key)

    cached = store.load_cache(site_key)
    print(
        f"\n[{site['name']}] {len(cached)} recipes already cached",
        file=sys.stderr,
    )

    # --- URL discovery ---
    if site["discovery"] == "category":
        url_cuisine_pairs = discover_via_categories(
            site["categories"], site["max_pages"], site["delay"]
        )
        print(
            f"  Discovered {len(url_cuisine_pairs)} candidate URLs",
            file=sys.stderr,
        )
    elif site["discovery"] == "sitemap":
        import re

        pattern = re.compile(site["url_pattern"]) if site.get("url_pattern") else None
        urls = discover_via_sitemap(
            site["sitemap_index_url"], url_filter=pattern, delay=site["delay"]
        )
        default_cuisine = site.get("cuisine_default", "Unknown")
        url_cuisine_pairs = [(u, default_cuisine) for u in urls]
        print(
            f"  Discovered {len(url_cuisine_pairs)} candidate URLs via sitemap",
            file=sys.stderr,
        )
    else:
        print(
            f"  [ERROR] Unknown discovery method: {site['discovery']}", file=sys.stderr
        )
        return 0

    # --- Scrape new URLs ---
    new_count = 0
    seen_ids = {r["id"] for r in cached.values()}

    for url, cuisine in url_cuisine_pairs:
        if url in cached:
            continue
        if limit is not None and new_count >= limit:
            print(f"  Reached --limit {limit}", file=sys.stderr)
            break

        html_text = fetch(url, delay=site["delay"])
        if not html_text:
            continue

        jsonld = find_recipe_jsonld(html_text)
        if not jsonld:
            print(f"  [NO JSON-LD] {url}", file=sys.stderr)
            continue

        recipe = map_to_recipe(jsonld, site["name"], cuisine, url)
        if not recipe:
            print(f"  [SKIP] {url} — missing name or ingredients", file=sys.stderr)
            continue

        if recipe["id"] in seen_ids:
            print(f"  [DUP id] {recipe['id']} — {url}", file=sys.stderr)
            seen_ids.add(recipe["id"])
            store.append_to_cache(site_key, recipe)
            continue

        seen_ids.add(recipe["id"])
        store.append_to_cache(site_key, recipe)
        new_count += 1
        print(f"  [OK] {recipe['name']}", file=sys.stderr)

    print(
        f"  Done — {new_count} new recipes cached for {site['name']}",
        file=sys.stderr,
    )

    if write_staging:
        all_cached = list(store.load_cache(site_key).values())
        staging_file = store.write_staging(site_key, all_cached)
        print(
            f"  Staging written → {staging_file}  (review before adding to data.py)",
            file=sys.stderr,
        )

    return new_count


def main():
    parser = argparse.ArgumentParser(
        description="Recipe extraction pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--site", help="Site key to scrape (see --list-sites)")
    parser.add_argument(
        "--limit", type=int, help="Stop after N new recipes for this site"
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Ignore existing cache and re-scrape everything",
    )
    parser.add_argument(
        "--discover-only",
        action="store_true",
        help="Discover URLs only; do not fetch recipe pages",
    )
    parser.add_argument(
        "--no-staging",
        action="store_true",
        help="Skip writing pipeline/staging/<site>.py after scraping",
    )
    parser.add_argument(
        "--from-cache",
        action="store_true",
        help="Emit data.py from all cached recipes (no network requests)",
    )
    parser.add_argument(
        "--output",
        help="Write data.py to this path (default: stdout). Use with --from-cache.",
    )
    parser.add_argument(
        "--list-sites", action="store_true", help="List configured sites and exit"
    )
    args = parser.parse_args()

    if args.list_sites:
        print("Configured sites:")
        for key, site in SITES.items():
            print(f"  {key:25s}  {site['name']}")
        return

    if args.from_cache:
        recipes = store.load_all_caches()
        print(f"Loaded {len(recipes)} recipes from cache.", file=sys.stderr)
        output = store.emit_data_py(recipes)
        if args.output:
            pathlib.Path(args.output).write_text(output)
            print(f"Written to {args.output}", file=sys.stderr)
        else:
            print(output)
        return

    if not args.site:
        parser.error("--site is required (or use --from-cache / --list-sites)")

    if args.site not in SITES:
        print(
            f"Unknown site '{args.site}'. Run with --list-sites to see options.",
            file=sys.stderr,
        )
        sys.exit(1)

    site = SITES[args.site]

    if args.discover_only:
        count = 0
        if site["discovery"] == "category":
            pairs = discover_via_categories(
                site["categories"], site["max_pages"], site["delay"]
            )
            for url, cuisine in pairs:
                print(f"{cuisine}\t{url}")
            count = len(pairs)
        elif site["discovery"] == "sitemap":
            import re

            pattern = (
                re.compile(site["url_pattern"]) if site.get("url_pattern") else None
            )
            urls = discover_via_sitemap(
                site["sitemap_index_url"], url_filter=pattern, delay=site["delay"]
            )
            for url in urls:
                print(url)
            count = len(urls)
        print(f"\n{count} URLs found.", file=sys.stderr)
        return

    _scrape_site(
        args.site, site, args.limit, args.no_cache, write_staging=not args.no_staging
    )


if __name__ == "__main__":
    main()
