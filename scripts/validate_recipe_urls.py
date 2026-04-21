#!/usr/bin/env python3
"""
Validate recipe source URLs by checking page content matches recipe name.

Usage:
  uv run python scripts/validate_recipe_urls.py [--only-problems] [--id RECIPE_ID] [--threshold 0.60]
"""

import sys
import pathlib
import urllib.request
import urllib.error
import html.parser
import difflib
import re
import time
import json
import argparse
import socket
import unicodedata
from typing import NamedTuple, Optional
from collections import defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from app.recipes.data import RECIPES

TITLE_SUFFIXES = [
    r"\s*[|\-–—]\s*Rasa Malaysia.*",
    r"\s*[|\-–—]\s*The Woks of Life.*",
    r"\s*[|\-–—]\s*Panlasang Pinoy.*",
    r"\s*[|\-–—]\s*Made With Lau.*",
    r"\s*[|\-–—]\s*Hungry Huy.*",
    r"\s*[|\-–—]\s*Cooking Therapy.*",
    r"\s*[|\-–—]\s*I Am A Foodie.*",
    r"\s*[|\-–—]\s*Glebe Kitchen.*",
    r"\s*[|\-–—]\s*Vicky Pham.*",
    r"\s*[|\-–—]\s*iamafoodblog.*",
    r"\s*[|\-–—]\s*Nyonya Cooking.*",
    r"\s*[|\-–—]\s*RecipeTin Eats.*",
    r"\s*[|\-–—]\s*Huang Kitchen.*",
    r"\s*[|\-–—]\s*Delightful Plate.*",
    r"\s*[|\-–—]\s*Hot Thai Kitchen.*",
    r"\s*[|\-–—]\s*Cook Me Indonesian.*",
    r"\s*[|\-–—]\s*Daily Cooking Quest.*",
    r"\s*[|\-–—]\s*What To Cook Today.*",
    r"\s*Recipe$",
]

# Known alternate titles/transliterations for recipe names.
# When a recipe name matches a key, its aliases are also accepted.
RECIPE_ALIASES: dict[str, list[str]] = {
    "Pho Bo": ["Pho", "Vietnamese Noodle Soup", "Pho Vietnamese Noodle Soup"],
    "Pho Ga": ["Chicken Pho", "20-Minute Chicken Pho"],
    "Bo Kho": ["Bo Kho", "Bho Kho", "Vietnamese Beef Stew"],
    "Bun Bo Hue": [
        "Bun Bo Hue",
        "Bún Bò Huế",
        "Spicy Vietnamese Beef",
        "Spicy Beef Pork Noodle",
    ],
    "Banh Xeo": [
        "Banh Xeo",
        "Bánh Xèo",
        "Vietnamese Crepes",
        "Vietnamese Pancakes",
        "Crispy Vietnamese",
    ],
    "Goi Cuon": ["Goi Cuon", "Gỏi Cuốn", "Vietnamese Spring Rolls"],
    "Ca Kho To": [
        "Ca Kho To",
        "Cá Kho Tộ",
        "Vietnamese Braised Fish",
        "Vietnamese Caramelized",
        "Braised Catfish",
    ],
    "Bun Cha": ["Bun Cha", "Bún Chả", "Vietnamese Grilled Pork", "Authentic Bun Cha"],
    "Com Tam": ["Com Tam", "Cơm Tấm", "Broken Rice", "Authentic Com Tam"],
    "Cha Ca La Vong": [
        "Cha Ca",
        "Chả Cá",
        "Hanoi Fried Fish",
        "Turmeric Dill",
        "Chả Cá Lã Vọng",
        "Cha Ca La Vong",
    ],
    "Som Tam": ["Som Tam", "Green Papaya Salad", "Thai Green Papaya"],
    "Pad See Ew": ["Pad See Ew", "Thai Rice Noodles"],
    "Pan Mee": ["Pan Mee", "Hakka Flat Noodle"],
    "Rawon": ["Rawon", "East Javanese Beef Stew"],
    "Pecel": ["Pecel", "Javanese Peanut Sauce", "Pecel Sayur"],
    "Chee Cheong Fun": ["Chee Cheong Fun", "Cheung Fun", "Rice Noodle"],
    "Bak Kut Teh": ["Bak Kut Teh", "Pork Ribs Tea", "Ultimate Guide"],
    "Gado-Gado": ["Gado-Gado", "Gado Gado", "Indonesian salad", "peanut sauce"],
}

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"


class ValidationResult(NamedTuple):
    recipe_id: str
    recipe_name: str
    source_url: str
    status: str
    title_found: str
    h1_found: str
    score: float
    detail: str


class HTMLExtractor(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = None
        self.h1 = None
        self.body_text = []
        self.in_title = False
        self.in_h1 = False
        self.in_body = False
        self.body_char_count = 0

    def handle_starttag(self, tag, attrs):
        if tag == "title":
            self.in_title = True
        elif tag == "h1":
            self.in_h1 = True
        elif tag in ("p", "div", "article", "section"):
            self.in_body = True

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        elif tag == "h1":
            self.in_h1 = False
        elif tag in ("p", "div", "article", "section"):
            self.in_body = False

    def handle_data(self, data):
        text = data.strip()
        if not text:
            return

        if self.in_title and self.title is None:
            self.title = text

        if self.in_h1 and self.h1 is None:
            self.h1 = text

        if self.in_body and self.body_char_count < 5000:
            self.body_text.append(text)
            self.body_char_count += len(text)


def strip_title_suffix(title: str) -> str:
    for suffix in TITLE_SUFFIXES:
        title = re.sub(suffix, "", title, flags=re.IGNORECASE)
    return title.strip()


def _normalize(s: str) -> str:
    return (
        unicodedata.normalize("NFKD", s)
        .encode("ascii", "ignore")
        .decode()
        .lower()
        .strip()
    )


def similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, _normalize(a), _normalize(b)).ratio()


def fetch_and_extract(
    url: str, timeout: int = 15
) -> tuple[Optional[str], Optional[str], Optional[str]]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            html_content = response.read().decode("utf-8", errors="ignore")

        parser = HTMLExtractor()
        parser.feed(html_content)

        title = parser.title
        h1 = parser.h1
        body = " ".join(parser.body_text)

        if title:
            title = strip_title_suffix(title)

        return title, h1, body
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"URL Error: {e.reason}")
    except socket.timeout:
        raise RuntimeError("Timeout")
    except Exception as e:
        raise RuntimeError(f"Error: {e}")


def validate_recipe(recipe: dict, threshold: float = 0.60) -> ValidationResult:
    recipe_id = recipe["id"]
    recipe_name = recipe["name"]
    source_url = recipe["source_url"]

    try:
        title, h1, body = fetch_and_extract(source_url)
    except RuntimeError as e:
        return ValidationResult(
            recipe_id=recipe_id,
            recipe_name=recipe_name,
            source_url=source_url,
            status="ERROR",
            title_found="",
            h1_found="",
            score=0.0,
            detail=str(e),
        )

    title_score = 0.0
    h1_score = 0.0

    if title:
        title_score = similarity(recipe_name, title)

    if h1:
        h1_score = similarity(recipe_name, h1)

    # Also score against known aliases (transliterations, alternate titles).
    # Use substring containment as a fallback for long descriptive titles.
    aliases = RECIPE_ALIASES.get(recipe_name, [])
    for alias in aliases:
        for text, score_var in [(title, "title"), (h1, "h1")]:
            if not text:
                continue
            s = similarity(alias, text)
            # Also treat as a match if the alias appears verbatim inside the title
            if s < threshold and _normalize(alias) in _normalize(text):
                s = threshold
            if s >= threshold:
                if score_var == "title":
                    title_score = max(title_score, s)
                else:
                    h1_score = max(h1_score, s)

    best_score = max(title_score, h1_score)

    if best_score >= threshold:
        match_from = "title" if title_score >= h1_score else "h1"
        return ValidationResult(
            recipe_id=recipe_id,
            recipe_name=recipe_name,
            source_url=source_url,
            status="OK",
            title_found=title or "",
            h1_found=h1 or "",
            score=best_score,
            detail=f"{match_from}: {best_score:.2f}",
        )

    keywords_in_body = body and any(
        word.lower() in body.lower() for word in recipe_name.split() if len(word) > 3
    )

    if keywords_in_body:
        return ValidationResult(
            recipe_id=recipe_id,
            recipe_name=recipe_name,
            source_url=source_url,
            status="WEAK_MATCH",
            title_found=title or "",
            h1_found=h1 or "",
            score=0.0,
            detail="keywords found in body",
        )

    actual_content = f"title: '{title}'" if title else "no title"
    if h1:
        actual_content += f" | h1: '{h1}'"

    return ValidationResult(
        recipe_id=recipe_id,
        recipe_name=recipe_name,
        source_url=source_url,
        status="MISMATCH",
        title_found=title or "",
        h1_found=h1 or "",
        score=best_score,
        detail=actual_content,
    )


def run_validation(
    recipes: list,
    filter_id: Optional[str] = None,
    threshold: float = 0.60,
    delay: float = 1.5,
):
    if filter_id:
        recipes = [r for r in recipes if r["id"] == filter_id]
        if not recipes:
            print(f"Recipe '{filter_id}' not found")
            return []

    results = []
    last_fetch_time = defaultdict(float)

    for i, recipe in enumerate(recipes, 1):
        domain = urllib.parse.urlparse(recipe["source_url"]).netloc
        elapsed = time.time() - last_fetch_time.get(domain, 0)
        if elapsed < delay:
            time.sleep(delay - elapsed)

        print(f"[{i}/{len(recipes)}] {recipe['id']}...", end=" ", flush=True)
        result = validate_recipe(recipe, threshold)
        results.append(result)
        last_fetch_time[domain] = time.time()
        print(result.status)

    return results


def print_results(results: list, only_problems: bool = False):
    print("\n" + "=" * 120)
    print(f"{'Status':<12} {'Recipe ID':<25} {'Recipe Name':<30} {'Details':<53}")
    print("=" * 120)

    for result in results:
        if only_problems and result.status == "OK":
            continue

        print(
            f"[{result.status:<10}] {result.recipe_id:<25} {result.recipe_name:<30} {result.detail:<53}"
        )

    print("=" * 120)

    counts = defaultdict(int)
    for result in results:
        counts[result.status] += 1

    print(
        f"\nSummary: {counts['OK']} OK, {counts['WEAK_MATCH']} WEAK_MATCH, {counts['MISMATCH']} MISMATCH, {counts['ERROR']} ERROR"
    )


def save_json_report(results: list, filename: str):
    data = [
        {
            "recipe_id": r.recipe_id,
            "recipe_name": r.recipe_name,
            "source_url": r.source_url,
            "status": r.status,
            "title_found": r.title_found,
            "h1_found": r.h1_found,
            "score": r.score,
            "detail": r.detail,
        }
        for r in results
    ]
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    print(f"\nJSON report saved to {filename}")


def main():
    parser = argparse.ArgumentParser(description="Validate recipe source URLs")
    parser.add_argument("--only-problems", action="store_true", help="Hide OK results")
    parser.add_argument("--output", type=str, help="Write JSON report to file")
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.60,
        help="Fuzzy match threshold (default 0.60)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.5,
        help="Per-domain delay in seconds (default 1.5)",
    )
    parser.add_argument("--id", type=str, help="Validate a single recipe by ID")

    args = parser.parse_args()

    results = run_validation(
        RECIPES, filter_id=args.id, threshold=args.threshold, delay=args.delay
    )
    print_results(results, only_problems=args.only_problems)

    if args.output:
        save_json_report(results, args.output)


if __name__ == "__main__":
    import urllib.parse

    main()
