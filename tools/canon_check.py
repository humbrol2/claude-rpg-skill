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

    # Direct hit
    if key in registry["entities"]:
        return {"resolved_via": "name", "entity": registry["entities"][key]}

    # Alias hit
    if key in registry["by_alias"]:
        target_key = registry["by_alias"][key]
        return {"resolved_via": "alias", "entity": registry["entities"][target_key]}

    # Substring fallback (last resort, weak match) — also covers campaign
    # naming conventions like heritage suffixes ("name-vor" vs "name").
    candidates = []
    for k, ent in registry["entities"].items():
        if key in k or k in key:
            candidates.append(ent)
    if len(candidates) == 1:
        return {"resolved_via": "substring", "entity": candidates[0]}
    if len(candidates) > 1:
        return {"resolved_via": "ambiguous", "candidates": [c["name"] for c in candidates]}

    return None


def scene_context(memory_dir: Path, place: str) -> str:
    """Who and what canon ties to a location, with the file each fact came from.

    Run before narrating a scene at a known place so the narrator leads with
    what is already established instead of inventing. Matches the place's
    name or aliases against every canon file's frontmatter and body.
    """
    hit = lookup(memory_dir, place)
    if hit is None or hit.get("resolved_via") == "ambiguous":
        return f"NOT FOUND / AMBIGUOUS: '{place}'. Canon-check the name first."
    loc = hit["entity"]
    # Short aliases ("hotel", "the bar") match half the campaign; only names
    # specific enough to be a real anchor count for the scan.
    MIN_ANCHOR_CHARS = 6
    names = {normalize_name(loc["name"])} | {
        normalize_name(a) for a in loc.get("frontmatter", {}).get("aliases", []) or []
        if len(normalize_name(a)) >= MIN_ANCHOR_CHARS}
    MAX_MATCHES = 25
    out = [f"SCENE: {loc['name']} ({loc['file']}) — {loc['description']}"]
    fm = loc.get("frontmatter", {})
    for field in ("status", "faction", "defer_to_user_on"):
        if fm.get(field):
            out.append(f"  {field}: {fm[field]}")
    out.append("Canon that mentions this place:")
    found = 0
    for path in sorted(memory_dir.glob("*.md")):
        if path.name in (loc["file"], "MEMORY.md"):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        norm = normalize_name(text)
        if not any(n in norm for n in names):
            continue
        from common import parse_frontmatter
        efm, body = parse_frontmatter(text)
        if not efm:
            continue
        found += 1
        bits = [f"  - {efm.get('name', path.stem)} ({path.name})"]
        for field in ("status", "read_in_tier", "relationships"):
            if efm.get(field):
                bits.append(f"{field}={efm[field]}")
        # the first body line that names the place, as the source anchor
        for line in body.splitlines():
            if any(n in normalize_name(line) for n in names):
                bits.append(f'| "{line.strip()[:140]}"')
                break
        out.append(" ".join(bits))
        if found >= MAX_MATCHES:
            out.append("  … more; narrow with a more specific name")
            break
    if not found:
        out.append("  (none — nothing else on file ties to this place)")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("--memory-dir", type=Path, default=None)
    ap.add_argument("--json", action="store_true", help="Output JSON")
    ap.add_argument("--scene", action="store_true",
                    help="treat NAME as a location and list every canon entry tied to it")
    args = ap.parse_args()

    memory_dir = args.memory_dir or find_memory_dir()
    if args.scene:
        print(scene_context(memory_dir, args.name))
        return 0
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
