#!/usr/bin/env python3
"""Look up an entity in the campaign registry. Returns canon facts or 'NOT FOUND'.

Usage: python canon_check.py <name> [--memory-dir PATH]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import find_memory_dir
from registry_build import build_registry, normalize_name


def lookup(memory_dir: Path, name: str) -> dict | None:
    registry_path = memory_dir / "registry.json"
    if registry_path.exists():
        with open(registry_path, "r", encoding="utf-8") as f:
            registry = json.load(f)
    else:
        registry = build_registry(memory_dir)

    key = normalize_name(name)

    # Strip Drakari heritage suffixes for the bare-name search
    bare = key
    for suffix in ["-vor-korr-threll", "-vor-korr", "-vor", "-korr-threll", "-korr",
                   "-threll", "-saen", "-vellith", "-daresh", "-khorr"]:
        if bare.endswith(suffix):
            bare = bare[: -len(suffix)]
            break

    # Direct hit
    if key in registry["entities"]:
        return {"resolved_via": "name", "entity": registry["entities"][key]}

    # Bare-name hit (strip heritage suffix)
    if bare != key and bare in registry["entities"]:
        return {"resolved_via": "name_stripped_suffix", "entity": registry["entities"][bare]}

    # Alias hit
    if key in registry["by_alias"]:
        target_key = registry["by_alias"][key]
        return {"resolved_via": "alias", "entity": registry["entities"][target_key]}

    if bare != key and bare in registry["by_alias"]:
        target_key = registry["by_alias"][bare]
        return {"resolved_via": "alias_stripped_suffix", "entity": registry["entities"][target_key]}

    # Substring fallback (last resort, weak match)
    candidates = []
    for k, ent in registry["entities"].items():
        if bare in k or k in bare:
            candidates.append(ent)
    if len(candidates) == 1:
        return {"resolved_via": "substring", "entity": candidates[0]}
    if len(candidates) > 1:
        return {"resolved_via": "ambiguous", "candidates": [c["name"] for c in candidates]}

    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("--memory-dir", type=Path, default=None)
    ap.add_argument("--json", action="store_true", help="Output JSON")
    args = ap.parse_args()

    memory_dir = args.memory_dir or find_memory_dir()
    result = lookup(memory_dir, args.name)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result else 1

    if result is None:
        print(f"NOT FOUND: '{args.name}' has no canon entry.")
        print("ACTION: Ask the user about this entity. Do not invent.")
        return 1

    if result.get("resolved_via") == "ambiguous":
        print(f"AMBIGUOUS: '{args.name}' matches multiple entries:")
        for c in result["candidates"]:
            print(f"  - {c}")
        print("ACTION: Disambiguate with the user.")
        return 1

    entity = result["entity"]
    print(f"FOUND: {entity['name']} (via {result['resolved_via']})")
    print(f"  File: {entity['file']}")
    print(f"  Type: {entity['type']}")
    print(f"  Description: {entity['description']}")
    fm = entity.get("frontmatter", {})
    for field in ("species", "faction", "status", "read_in_tier", "relationships",
                  "aliases", "defer_to_user_on"):
        val = fm.get(field)
        if val:
            label = field.replace("_", " ").upper() if field == "defer_to_user_on" else field.title()
            print(f"  {label}: {val}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
