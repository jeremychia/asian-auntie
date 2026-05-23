"""
YouTube channel recipe extraction.

Uses yt-dlp to discover videos and fetch transcripts/descriptions,
then the Anthropic API to extract and translate structured recipe data.

Site config schema (discovery="youtube"):
  channel_url   str    — YouTube channel URL (e.g. https://www.youtube.com/@channel/videos)
  cuisine       str    — Cuisine label applied to all videos from this channel
  delay         float  — Seconds to sleep between API calls
  max_videos    int    — Cap on videos to discover (optional)
"""

import os
import re
import json
import sys
import time
import urllib.request
from datetime import datetime
from typing import Optional


def _log(msg: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"  [{ts}] {msg}", file=sys.stderr, flush=True)


from pipeline.transform import (  # noqa: E402
    clean_ingredient,
    format_cook_time,
    infer_difficulty,
    slugify,
)


def _yt_dlp():
    try:
        import yt_dlp

        return yt_dlp
    except ImportError:
        raise ImportError(
            "yt-dlp is required for YouTube extraction.\n"
            "Install with: uv add yt-dlp --project pipeline"
        )


def _anthropic():
    try:
        import anthropic

        return anthropic
    except ImportError:
        raise ImportError(
            "anthropic is required for YouTube extraction.\n"
            "Install with: uv add anthropic --project pipeline"
        )


# ── Discovery ──────────────────────────────────────────────────────────────────


def discover_channel_videos(
    channel_url: str,
    max_videos: Optional[int] = None,
    delay: float = 1.0,
) -> list[str]:
    """Return a list of video URLs from a YouTube channel."""
    yt = _yt_dlp()

    ydl_opts = {
        "extract_flat": "in_playlist",
        "quiet": True,
        "no_warnings": True,
    }
    if max_videos:
        ydl_opts["playlistend"] = max_videos

    with yt.YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(channel_url, download=False)

    if not result or "entries" not in result:
        return []

    urls = []
    for entry in result["entries"] or []:
        if not entry:
            continue
        video_id = entry.get("id")
        if video_id:
            urls.append(f"https://www.youtube.com/watch?v={video_id}")
        if max_videos and len(urls) >= max_videos:
            break

    return urls


# ── Transcript fetching ────────────────────────────────────────────────────────


def _fetch_vtt(url: str) -> str:
    """Fetch a VTT subtitle URL and return deduplicated plain text."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8")
    except Exception:
        return ""

    lines = []
    prev = None
    for line in raw.splitlines():
        line = line.strip()
        # Skip header, blank lines, and timestamp cue lines
        if not line or line.startswith("WEBVTT") or "-->" in line:
            continue
        # Strip VTT inline tags (<c.color...>, <b>, etc.) and position metadata
        line = re.sub(r"<[^>]+>", "", line).strip()
        if line and line != prev:
            lines.append(line)
            prev = line

    return " ".join(lines)


def _get_video_data(video_url: str) -> dict:
    """Return metadata + description + transcript for a YouTube video."""
    yt = _yt_dlp()
    _log(f"Fetching  {video_url}")

    with yt.YoutubeDL(
        {"skip_download": True, "quiet": True, "no_warnings": True}
    ) as ydl:
        info = ydl.extract_info(video_url, download=False)

    title = info.get("title", "")
    description = info.get("description") or ""
    duration_secs = info.get("duration")

    # Prefer auto-generated captions in the original language. Skip translated
    # tracks (marked with a language suffix like "my-orig" is the original;
    # "en" would be a translated version — we want the source language so
    # Claude can translate it rather than getting Google's machine translation).
    transcript = ""
    for caption_dict in (
        info.get("automatic_captions") or {},
        info.get("subtitles") or {},
    ):
        for lang, formats in caption_dict.items():
            if not formats:
                continue
            # Prefer vtt over json3 for simpler parsing
            for fmt in sorted(formats, key=lambda f: (f.get("ext") != "vtt")):
                if fmt.get("url"):
                    transcript = _fetch_vtt(fmt["url"])
                    if transcript:
                        break
            if transcript:
                break
        if transcript:
            break

    return {
        "title": title,
        "description": description,
        "duration_secs": duration_secs,
        "transcript": transcript,
    }


# ── LLM extraction ─────────────────────────────────────────────────────────────

_EXTRACT_PROMPT = """\
You are extracting a recipe from a YouTube cooking video. The video may be in any language — translate everything to English.

Video title: {title}

Video description:
{description}

Video transcript (auto-generated captions):
{transcript}

Extract the recipe and return a JSON object with exactly these fields:
{{
  "name": "<recipe name in English>",
  "ingredients": ["<ingredient with quantity if mentioned>", ...],
  "cook_time_minutes": <integer or null>,
  "notes": "<brief notes or empty string>"
}}

Rules:
- name: English translation of the recipe name. If the title contains the recipe name, use that.
- ingredients: each item should be an ingredient with quantity/unit if mentioned (e.g. "2 tbsp fish sauce", "3 cloves garlic"). Include all ingredients found.
- cook_time_minutes: total active cooking time in minutes. Use prep+cook if both given. Use midpoint for ranges. null if not mentioned.
- If the description contains a clear ingredient list, prefer it over the transcript.
- If neither source contains recipe content (e.g. a vlog, not a cooking video), return {{"name": "<title>", "ingredients": [], "cook_time_minutes": null, "notes": "no recipe found"}}.

Return only the JSON object, no other text."""


def extract_recipe_llm(
    video_data: dict,
    source_name: str,
    cuisine: str,
    video_url: str,
) -> Optional[dict]:
    """Use Claude to extract a recipe from video metadata + transcript."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is not set")

    anthropic = _anthropic()
    client = anthropic.Anthropic(api_key=api_key)

    # Truncate to stay within a reasonable token budget
    description = (video_data["description"] or "")[:2000]
    transcript = (video_data["transcript"] or "")[:4000]

    if not description:
        description = "(no description)"
    if not transcript:
        transcript = "(no transcript available)"

    prompt = _EXTRACT_PROMPT.format(
        title=video_data["title"],
        description=description,
        transcript=transcript,
    )

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    response_text = message.content[0].text.strip()

    try:
        extracted = json.loads(response_text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if not match:
            return None
        try:
            extracted = json.loads(match.group())
        except json.JSONDecodeError:
            return None

    name = (extracted.get("name") or "").strip() or video_data["title"]
    raw_ingredients = extracted.get("ingredients") or []

    if not raw_ingredients:
        return None

    ingredients = [clean_ingredient(i) for i in raw_ingredients]
    ingredients = [i for i in ingredients if i]
    if not ingredients:
        return None

    cook_time_minutes = extracted.get("cook_time_minutes")

    return {
        "id": slugify(name),
        "name": name,
        "source": source_name,
        "source_url": video_url,
        "cuisine": cuisine,
        "cook_time": format_cook_time(cook_time_minutes),
        "difficulty": infer_difficulty(cook_time_minutes),
        "ingredients": ingredients,
    }


# ── Description-based extraction (no LLM) ──────────────────────────────────────

# Lines that mark the start of an ingredient block (use as start trigger).
_INGR_HEADING_RE = re.compile(r"^for\s+(?:the\b|\w+ing\b)", re.IGNORECASE)
# Lines that are section headers within a block — skip when collecting.
_SECTION_HEADER_RE = re.compile(
    r"^(?:for\s+(?:the\b|\w+ing\b)|(?:main\s+|other\s+)?ingredients|ingredient\s+list|to\s+(?:garnish|serve|taste)\b|serves?\s+\d)",
    re.IGNORECASE,
)
# Block-level separators that terminate ingredient collection.
_SEPARATOR_RE = re.compile(r"^(?:-{3,}|={3,})$")
# Decorative lines made entirely of dashes, em-dashes, bullets etc. — skip.
_DECORATIVE_LINE_RE = re.compile(r"^[\-—–━─●•*=\s]+$")
_COOK_TIME_RE = re.compile(r"(\d+)\s*(?:to\s*\d+\s*)?(?:minutes?|mins?)", re.IGNORECASE)


def extract_recipe_description(
    video_data: dict,
    source_name: str,
    cuisine: str,
    video_url: str,
) -> Optional[dict]:
    """Parse ingredients directly from the video description — no LLM needed.

    Expects descriptions that contain an 'Ingredients' heading followed by
    ingredient lines, as used by Spice N Pans.
    """
    description = video_data.get("description") or ""
    title = video_data.get("title") or ""

    lines = description.splitlines()

    # "Serves X pax" is intentionally NOT used as a start trigger — it precedes
    # ingredient sections and would swallow the real heading into the skip filter.
    ingr_start = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.lower() in ("ingredients", "main ingredients", "ingredient list"):
            ingr_start = i + 1
            break
        if _INGR_HEADING_RE.match(stripped):
            ingr_start = i
            break

    if ingr_start is None:
        return None

    raw_ingredients = []
    for line in lines[ingr_start:]:
        stripped = line.strip()
        if _SEPARATOR_RE.match(stripped):
            break
        if not stripped:
            continue
        if _SECTION_HEADER_RE.match(stripped):
            continue
        if _DECORATIVE_LINE_RE.match(stripped) and len(stripped) >= 3:
            continue
        if "http" in stripped or stripped.startswith("www."):
            continue
        raw_ingredients.append(stripped)

    if not raw_ingredients:
        return None

    ingredients = [clean_ingredient(i) for i in raw_ingredients]
    ingredients = [i for i in ingredients if i]
    if not ingredients:
        return None

    preamble = "\n".join(lines[:ingr_start])
    cook_time_minutes = None
    m = _COOK_TIME_RE.search(preamble)
    if m:
        cook_time_minutes = int(m.group(1))

    name = title.strip() or source_name
    ascii_name = re.sub(r"[^\x00-\x7F]+", " ", name).strip()

    return {
        "id": slugify(ascii_name or name),
        "name": name,
        "source": source_name,
        "source_url": video_url,
        "cuisine": cuisine,
        "cook_time": format_cook_time(cook_time_minutes),
        "difficulty": infer_difficulty(cook_time_minutes),
        "ingredients": ingredients,
    }


# ── Public entry point ─────────────────────────────────────────────────────────


def scrape_video(
    video_url: str,
    source_name: str,
    cuisine: str,
    delay: float = 1.0,
    extraction: str = "llm",
) -> Optional[dict]:
    """Fetch a single YouTube video and return a recipe dict, or None."""
    video_data = _get_video_data(video_url)
    time.sleep(delay)
    _log(f"Extracting {video_url}")
    if extraction == "description":
        result = extract_recipe_description(video_data, source_name, cuisine, video_url)
    else:
        result = extract_recipe_llm(video_data, source_name, cuisine, video_url)
    if result:
        _log(f"Got recipe: {result['name'][:60]}")
    else:
        _log(f"No recipe:  {video_url}")
    return result
