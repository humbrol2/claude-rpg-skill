#!/usr/bin/env python3
"""Build memory_dir/registry.json from all memory files. Fast-lookup index of canon.

Usage: python registry_build.py [--memory-dir PATH]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import find_memory_dir, list_memory_files, parse_frontmatter


def normalize_name(name: str) -> str:
    return name.strip().lower()


def extract_roster_entities(path: Path, body: str) -> list[dict]:
    """Scan a roster file's body for per-entity bold sections like '**Name** — ...'.

    Returns list of {name, blurb, line_start} for each detected entity heading.
    """
    import re
    found = []
    pattern = re.compile(r"^\*\*([A-Z][A-Za-z0-9_'\- ]+?)\*\*\s*[—\-]\s*(.+?)$", re.MULTILINE)
    for match in pattern.finditer(body):
        name = match.group(1).strip()
        # Strip trailing italicized role descriptors and asterisks
        blurb_raw = match.group(2).strip().rstrip(".*")
        blurb = blurb_raw.strip("*").strip()
        found.append({"name": name, "blurb": blurb, "file": path.name})
    return found


def build_registry(memory_dir: Path) -> dict:
    entities = {}
    by_alias = {}
    by_type = {}

    for path in list_memory_files(memory_dir):
        text = path.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(text)
        if not fm:
            continue

        # Primary entry for the file itself
        entity = {
            "file": path.name,
            "name": fm.get("name", path.stem),
            "type": fm.get("type", "unknown"),
            "description": fm.get("description", ""),
            "frontmatter": fm,
        }

        key = normalize_name(entity["name"])
        entities[key] = entity

        aliases = fm.get("aliases", [])
        if isinstance(aliases, list):
            for alias in aliases:
                by_alias[normalize_name(alias)] = key

        type_key = entity["type"]
        by_type.setdefault(type_key, []).append(entity["name"])

        # Roster expansion — extract per-entity sections from the body
        # Triggered if frontmatter description contains "roster" or filename has "roster"
        is_roster = (
            "roster" in fm.get("description", "").lower()
            or "roster" in path.name.lower()
            or "entities" in fm  # explicit declaration
        )
        if is_roster:
            roster_entries = extract_roster_entities(path, body)
            for sub in roster_entries:
                sub_key = normalize_name(sub["name"])
                # Don't overwrite existing primary entries
                if sub_key in entities:
                    continue
                sub_entity = {
                    "file": path.name,
                    "name": sub["name"],
                    "type": fm.get("type", "unknown") + "_roster_member",
                    "description": sub["blurb"][:200],
                    "frontmatter": {
                        "name": sub["name"],
                        "description": sub["blurb"][:200],
                        "type": fm.get("type", "unknown") + "_roster_member",
                        "parent_file": path.name,
                        "parent_roster": fm.get("name", path.stem),
                    },
                }
                entities[sub_key] = sub_entity
                by_type.setdefault(sub_entity["type"], []).append(sub["name"])

    return {
        "entities": entities,
        "by_alias": by_alias,
        "by_type": by_type,
        "count": len(entities),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--memory-dir", type=Path, default=None)
    args = ap.parse_args()

    memory_dir = args.memory_dir or find_memory_dir()
    registry = build_registry(memory_dir)

    out = memory_dir / "registry.json"
    tmp = out.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)
    tmp.replace(out)

    print(f"Built registry: {registry['count']} entities at {out}")
    print(f"  Types: {dict((t, len(v)) for t, v in registry['by_type'].items())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
