#!/usr/bin/env python3
"""Extract Toybox README categories and tools into ontology-ready JSON.

No third-party dependencies are required. The parser is intentionally conservative:
it only treats tool links found inside two-column table headers as canonical Tool
objects and associates them with the nearest H1/H3 catalog headings.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import unicodedata
from pathlib import Path

TOKEN_RE = re.compile(
    r"(?P<h1><h1\b[^>]*>.*?</h1>)|"
    r"(?P<h3><h3\b[^>]*>.*?</h3>)|"
    r"(?P<tool><th\b[^>]*colspan=[\"']2[\"'][^>]*>.*?</th>)",
    re.IGNORECASE | re.DOTALL,
)
LINK_RE = re.compile(r"<a\b[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", re.IGNORECASE | re.DOTALL)
TAG_RE = re.compile(r"<[^>]+>")


def plain(fragment: str) -> str:
    fragment = re.sub(r"<img\b[^>]*>", " ", fragment, flags=re.IGNORECASE)
    fragment = TAG_RE.sub(" ", fragment)
    fragment = html.unescape(fragment)
    return " ".join(fragment.split()).strip()


def slug(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return value or "unnamed"


def is_catalog_heading(name: str) -> bool:
    blocked = {
        "open source everything",
        "versioning",
        "mirrors",
        "legend",
        "table of contents",
    }
    return bool(name) and name.lower() not in blocked


def ingest(readme: Path) -> dict:
    text = readme.read_text(encoding="utf-8")
    current_category = None
    current_subcategory = None
    categories = {}
    tools = {}
    contains = []

    for match in TOKEN_RE.finditer(text):
        if match.group("h1"):
            name = plain(match.group("h1"))
            if is_catalog_heading(name):
                current_category = slug(name)
                current_subcategory = None
                categories.setdefault(
                    current_category,
                    {
                        "categoryId": current_category,
                        "name": name,
                        "status": "active",
                        "sourceUrl": "README.md",
                    },
                )
            else:
                current_category = None
                current_subcategory = None
            continue

        if match.group("h3"):
            current_subcategory = plain(match.group("h3")) or None
            continue

        if not current_category or not match.group("tool"):
            continue

        link = LINK_RE.search(match.group("tool"))
        if not link:
            continue

        homepage, raw_name = link.groups()
        name = plain(raw_name)
        if not name or homepage.startswith("#"):
            continue

        base_id = slug(name)
        tool_id = base_id
        suffix = 2
        while tool_id in tools and tools[tool_id].get("homepage") != homepage:
            tool_id = f"{base_id}-{suffix}"
            suffix += 1

        tool = tools.setdefault(
            tool_id,
            {
                "toolId": tool_id,
                "name": name,
                "homepage": homepage,
                "status": "active",
                "sourceUrl": "README.md",
                "sourceId": "toybox-readme",
                "categoryId": current_category,
            },
        )
        if current_subcategory:
            tool["subcategory"] = current_subcategory

        edge = {"categoryId": current_category, "toolId": tool_id}
        if edge not in contains:
            contains.append(edge)

    return {
        "ontology": "toybox",
        "objects": {
            "Category": list(categories.values()),
            "Tool": list(tools.values()),
        },
        "links": {"contains": contains},
        "stats": {"categories": len(categories), "tools": len(tools), "containsLinks": len(contains)},
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--readme", default="README.md")
    parser.add_argument("--output", default="ontology/generated/catalog.json")
    args = parser.parse_args()

    data = ingest(Path(args.readme))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(data["stats"], sort_keys=True))


if __name__ == "__main__":
    main()
