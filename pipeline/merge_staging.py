#!/usr/bin/env python3
"""
Merge a staging recipe file into app/recipes/data.py.

Rules:
  - Staging is authoritative for MWL-vs-MWL conflicts (same source).
  - Cross-source ID conflicts (e.g. Rasa Malaysia vs MWL): keep both;
    the existing non-MWL recipe gets a source-slug suffix on its ID.
  - URL matches (handles old "-lau" suffix IDs): staging wins.
  - Staging is deduped by ID; last occurrence wins (egg-drop-soup appears twice).
  - New staging recipes are appended in a Made with Lau section at the end.

Usage:
  python pipeline/merge_staging.py [--dry-run]
"""
import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STAGING = ROOT / "pipeline/staging/2026-04-25_made_with_lau.py"
DATA = ROOT / "app/recipes/data.py"

FIELD_ORDER = (
    "id",
    "name",
    "source",
    "source_url",
    "cuisine",
    "cook_time",
    "difficulty",
)

SECTION_ORDER = [
    "Malaysian",
    "Thai",
    "Filipino",
    "Indonesian",
    "Vietnamese",
    "Singaporean",
    "Chinese",
]


def load_recipes(path: Path) -> list[dict]:
    src = path.read_text()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "RECIPES":
                    return ast.literal_eval(node.value)
    raise ValueError(f"RECIPES not found in {path}")


def fmt_recipe(r: dict) -> str:
    lines = ["    {"]
    for key in FIELD_ORDER:
        lines.append(f'        "{key}": {r[key]!r},')
    lines.append('        "ingredients": [')
    for ing in r["ingredients"]:
        lines.append(f"            {ing!r},")
    lines.append("        ],")
    lines.append("    },")
    return "\n".join(lines)


SOURCE_SLUGS = {
    "Rasa Malaysia": "rm",
    "The Woks of Life": "twol",
    "Nyonya Cooking": "nyonya",
    "Panlasang Pinoy": "pp",
    "What To Cook Today": "wtct",
    "Caroline's Cooking": "cc",
    "RecipeTin Eats": "rte",
    "Daily Cooking Quest": "dcq",
    "Hungry Huy": "hh",
    "Vicky Pham": "vp",
    "Hot Thai Kitchen": "htk",
    "Delightful Plate": "dp",
    "Cook Me Indonesian": "cmi",
    "Huang Kitchen": "hk",
    "Lin's Food": "lf",
}


def source_slug(source: str) -> str:
    return SOURCE_SLUGS.get(source, source.lower().replace(" ", "-"))


def section_header(name: str) -> str:
    fill = "─" * max(0, 76 - len(name) - 1)
    return f"    # ── {name} {fill}"


def main(dry_run: bool = False) -> None:
    # Load + dedup staging by ID (last occurrence wins)
    staging_raw = load_recipes(STAGING)
    staging_by_id: dict[str, dict] = {}
    for r in staging_raw:
        staging_by_id[r["id"]] = r

    staging_ids = set(staging_by_id)
    staging_urls = {r["source_url"] for r in staging_by_id.values()}

    # Load existing data.py
    existing = load_recipes(DATA)

    # Partition existing recipes
    kept: list[dict] = []
    mwl_replaced: list[str] = []  # old MWL entries superseded by staging
    url_replaced: list[str] = []  # old -lau IDs replaced via URL match
    cross_renamed: list[tuple[str, str, str]] = []  # (old_id, new_id, source)

    for r in existing:
        if r["source_url"] in staging_urls:
            # URL match: staging covers this (handles old -lau suffix IDs)
            url_replaced.append(r["id"])
        elif r["id"] in staging_ids:
            if r["source"] == "Made with Lau":
                # Same source: staging's more-detailed version wins
                mwl_replaced.append(r["id"])
            else:
                # Cross-source conflict: keep existing under a new ID
                new_id = f"{r['id']}-{source_slug(r['source'])}"
                cross_renamed.append((r["id"], new_id, r["source"]))
                kept.append({**r, "id": new_id})
        else:
            kept.append(r)

    total_replaced = len(mwl_replaced) + len(url_replaced)
    new_count = (
        len(staging_by_id) - total_replaced
    )  # cross-renamed are additions, not replacements

    print(f"Existing recipes : {len(existing)}")
    print(f"Staging recipes  : {len(staging_by_id)} (deduped from {len(staging_raw)})")
    print(f"MWL superseded   : {len(mwl_replaced)}")
    for old_id in mwl_replaced:
        print(f"  - {old_id!r}")
    print(f"URL-replaced     : {len(url_replaced)}")
    for old_id in url_replaced:
        print(f"  - {old_id!r}")
    if cross_renamed:
        print(f"Cross-source (kept, ID renamed) : {len(cross_renamed)}")
        for old_id, new_id, src in cross_renamed:
            print(f"  - {old_id!r} → {new_id!r}  (from {src})")
    print(f"New MWL recipes  : {new_count}")
    print(f"Final total      : {len(kept) + len(staging_by_id)}")

    if dry_run:
        print("\n(dry-run — no file written)")
        return

    # Group kept recipes by cuisine, preserving relative order
    cuisine_groups: dict[str, list[dict]] = {}
    for r in kept:
        cuisine_groups.setdefault(r["cuisine"], []).append(r)

    # Build output lines
    out: list[str] = []
    out.append(
        "# Curated Malaysian and Southeast Asian recipe corpus.\n"
        "# Instructions are never stored here — we only hold enough metadata to compute\n"
        "# ingredient match % and link to the source.\n"
        "\n"
        "RECIPES = ["
    )

    # Known cuisines in preferred order
    for cuisine in SECTION_ORDER:
        recipes = cuisine_groups.pop(cuisine, [])
        if not recipes:
            continue
        out.append(section_header(cuisine))
        for r in recipes:
            out.append(fmt_recipe(r))

    # Any unexpected cuisines
    for cuisine, recipes in cuisine_groups.items():
        out.append(section_header(cuisine))
        for r in recipes:
            out.append(fmt_recipe(r))

    # Made with Lau block
    out.append(section_header("Made with Lau"))
    for r in staging_by_id.values():
        out.append(fmt_recipe(r))

    out.append("]")
    out.append("")

    DATA.write_text("\n".join(out))
    print(f"\nWritten → {DATA}")


if __name__ == "__main__":
    main(dry_run="--dry-run" in sys.argv)
