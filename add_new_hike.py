#!/usr/bin/env python3
"""Scaffold a new hike for the hiking page.

Run from the repo root:

    python add_new_hike.py

Prompts for the hike's metadata, creates `_hikes/<slug>.md` with that
metadata as YAML frontmatter, and creates the empty asset folders the
user then drops their GPX file (as `route.gpx`) and JPG photos into.
"""

from __future__ import annotations

import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
HIKES_DIR = REPO_ROOT / "_hikes"
GPX_DIR_TEMPLATE = REPO_ROOT / "assets" / "hikes" / "{slug}"
IMG_DIR_TEMPLATE = REPO_ROOT / "assets" / "img" / "hikes" / "{slug}"


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_bytes = normalized.encode("ascii", "ignore").decode("ascii")
    lowered = ascii_bytes.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    return slug


def prompt(
    message: str,
    validator=None,
    default: str | None = None,
    allow_empty: bool = False,
) -> str:
    suffix = f" [{default}]" if default else ""
    if allow_empty:
        suffix += " (optional)"
    while True:
        raw = input(f"{message}{suffix}: ").strip()
        if not raw and default is not None:
            raw = default
        if not raw:
            if allow_empty:
                return ""
            print("  (cannot be empty)")
            continue
        if validator is None:
            return raw
        try:
            return validator(raw)
        except ValueError as e:
            print(f"  ({e})")


def parse_date(raw: str) -> str:
    try:
        datetime.strptime(raw, "%Y-%m-%d")
    except ValueError:
        raise ValueError("expected YYYY-MM-DD")
    return raw


def parse_int(raw: str) -> int:
    try:
        return int(raw)
    except ValueError:
        raise ValueError("expected an integer")


def parse_float(raw: str) -> float:
    try:
        return float(raw)
    except ValueError:
        raise ValueError("expected a number")


def parse_rating(raw: str) -> float:
    try:
        n = float(raw)
    except ValueError:
        raise ValueError("expected a number")
    if not 1 <= n <= 5:
        raise ValueError("rating must be between 1 and 5")
    if (n * 2) != int(n * 2):
        raise ValueError("rating must be in 0.5 increments (e.g. 3, 3.5, 4)")
    return n


def format_rating(n: float) -> str:
    return str(int(n)) if n == int(n) else str(n)


def yaml_quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def write_markdown(path: Path, fields: dict) -> None:
    lines = ["---"]
    lines.append(f"name: {yaml_quote(fields['name'])}")
    lines.append(f"date: {yaml_quote(fields['date'])}")
    lines.append(f"vertical_distance: {fields['vertical_distance']}")
    lines.append(f"descent: {fields['descent']}")
    lines.append(f"total_distance: {fields['total_distance']}")
    lines.append(f"technical_difficulty: {yaml_quote(fields['technical_difficulty'])}")
    lines.append(f"start: {yaml_quote(fields['start'])}")
    lines.append(f"end: {yaml_quote(fields['end'])}")
    lines.append(f"rating: {format_rating(fields['rating'])}")
    if fields.get("comment"):
        lines.append(f"comment: {yaml_quote(fields['comment'])}")
    lines.append("---")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    print("Add a new hike\n--------------")

    name = prompt("Hike name (e.g. 'Sattel → Goldau')")
    slug = slugify(name)
    if not slug:
        print(
            "Could not derive a URL-safe slug from that name. Try something with ASCII letters."
        )
        return 1

    md_path = HIKES_DIR / f"{slug}.md"
    if md_path.exists():
        answer = input(
            f"  '{md_path.relative_to(REPO_ROOT)}' already exists. Overwrite? [y/N]: "
        ).strip().lower()
        if answer != "y":
            print("Aborted.")
            return 1

    today = datetime.now().strftime("%Y-%m-%d")
    date = prompt("Date (YYYY-MM-DD)", validator=parse_date, default=today)
    vertical = prompt("Vertical distance (m, ascent)", validator=parse_int)
    descent = prompt("Descent (m)", validator=parse_int)
    total = prompt("Total distance (km)", validator=parse_float)
    difficulty = prompt(
        "Technical difficulty (e.g. T1, T2, T3, T4, T5, T6)", default="T2"
    )
    start = prompt("Start (free text, e.g. 'Sattel-Aegeri (SZ)')")
    end = prompt("End   (free text, e.g. 'Goldau (SZ)')")
    rating = prompt("Rating (1-5, half steps OK e.g. 3.5)", validator=parse_rating)
    comment = prompt(
        "Comment (free text, leave blank to skip; edit the .md later for more)",
        allow_empty=True,
    )

    fields = {
        "name": name,
        "date": date,
        "vertical_distance": vertical,
        "descent": descent,
        "total_distance": total,
        "technical_difficulty": difficulty,
        "start": start,
        "end": end,
        "rating": rating,
        "comment": comment,
    }

    HIKES_DIR.mkdir(parents=True, exist_ok=True)
    write_markdown(md_path, fields)

    gpx_dir = Path(str(GPX_DIR_TEMPLATE).format(slug=slug))
    img_dir = Path(str(IMG_DIR_TEMPLATE).format(slug=slug))
    gpx_dir.mkdir(parents=True, exist_ok=True)
    img_dir.mkdir(parents=True, exist_ok=True)

    print()
    print(f"Created: {md_path.relative_to(REPO_ROOT)}")
    print(f"Created: {gpx_dir.relative_to(REPO_ROOT)}/")
    print(f"Created: {img_dir.relative_to(REPO_ROOT)}/")
    print()
    print("Next steps:")
    print(f"  1. Drop your GPX file in '{gpx_dir.relative_to(REPO_ROOT)}/'")
    print("     and rename it to 'route.gpx'.")
    print(f"  2. Drop your JPG photos in '{img_dir.relative_to(REPO_ROOT)}/'.")
    print(
        "     Name them so they sort the way you want them displayed "
        "(e.g. '01.jpg', '02.jpg'). The first one is the cover."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
