#!/usr/bin/env python3
"""Display the PC character sheet at memory_dir/state/character.json.

Usage: python character_view.py [--memory-dir PATH] [--section SECTION]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import find_memory_dir


def load_sheet(memory_dir: Path) -> dict | None:
    path = memory_dir / "state" / "character.json"
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def view_section(sheet: dict, section: str) -> None:
    val = sheet.get(section)
    if val is None:
        print(f"(no '{section}' section)")
        return
    if isinstance(val, list):
        if not val:
            print(f"  (empty)")
        for item in val:
            if isinstance(item, dict):
                primary = item.get("name") or item.get("title") or item.get("description") or json.dumps(item)
                print(f"  - {primary}")
                for k, v in item.items():
                    if k != "name":
                        print(f"      {k}: {v}")
            else:
                print(f"  - {item}")
    elif isinstance(val, dict):
        for k, v in val.items():
            print(f"  {k}: {v}")
    else:
        print(f"  {val}")


def view_all(sheet: dict) -> None:
    print(f"=== PC Character Sheet (Day {sheet.get('as_of_day', '?')}{', '+sheet.get('as_of_year') if sheet.get('as_of_year') else ''}) ===")

    name = sheet.get("true_name") or "<unset>"
    pronouns = sheet.get("pronouns") or ""
    species = sheet.get("species") or ""
    age = sheet.get("age") or ""
    desc = sheet.get("physical_description") or ""

    print(f"  True name: {name}")
    if pronouns:
        print(f"  Pronouns: {pronouns}")
    if species:
        print(f"  Species: {species}")
    if age:
        print(f"  Age: {age}")
    if desc:
        print(f"  Description: {desc}")
    print()

    covers = sheet.get("cover_identities", [])
    if covers:
        print(f"Cover identities ({len(covers)}):")
        for c in covers:
            if isinstance(c, dict):
                ctx = c.get("context", "")
                risk = c.get("compromise_risk", "")
                print(f"  - {c.get('name')}: {ctx}" + (f" (risk: {risk})" if risk else ""))
            else:
                print(f"  - {c}")
        print()

    heritage = sheet.get("heritage_standings", [])
    if heritage:
        print(f"Heritage standings ({len(heritage)}):")
        for h in heritage:
            if isinstance(h, dict):
                print(f"  - {h.get('title')}: {h.get('grantor')} (Day {h.get('granted_day', '?')})")
            else:
                print(f"  - {h}")
        print()

    attributes = sheet.get("attributes", {})
    if attributes:
        print("Attributes:")
        for k, v in attributes.items():
            print(f"  {k}: {v}")
        print()

    skills = sheet.get("skills", {})
    if skills:
        print("Skills:")
        for k, v in skills.items():
            print(f"  {k}: {v}")
        print()

    possessions = sheet.get("possessions", [])
    if possessions:
        print(f"Major possessions ({len(possessions)}):")
        for p in possessions:
            if isinstance(p, dict):
                print(f"  - {p.get('name')}: {p.get('description', '')}")
            else:
                print(f"  - {p}")
        print()

    carried = sheet.get("personal_items_carried", [])
    if carried:
        print(f"Items carried ({len(carried)}):")
        for item in carried:
            print(f"  - {item}")
        print()

    relationships = sheet.get("core_relationships", [])
    if relationships:
        print(f"Core relationships ({len(relationships)}):")
        for r in relationships:
            if isinstance(r, dict):
                tier = r.get("tier", "")
                kind = r.get("kind", "")
                print(f"  - {r.get('name')}: {kind}" + (f" [{tier}]" if tier else ""))
            else:
                print(f"  - {r}")
        print()

    goals = sheet.get("goals", {})
    if goals:
        for horizon, items in goals.items():
            if items:
                print(f"Goals ({horizon}):")
                for g in items:
                    print(f"  - {g}")
                print()

    anchors = sheet.get("history_anchors", [])
    if anchors:
        print(f"History anchors ({len(anchors)}):")
        for a in anchors:
            if isinstance(a, dict):
                print(f"  - Day {a.get('day', '?')}: {a.get('event', '')}")
            else:
                print(f"  - {a}")
        print()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--memory-dir", type=Path, default=None)
    ap.add_argument("--section", type=str, default=None, help="Show only one section")
    args = ap.parse_args()

    memory_dir = args.memory_dir or find_memory_dir()
    sheet = load_sheet(memory_dir)
    if sheet is None:
        print(f"No character sheet at {memory_dir}/state/character.json")
        print("Initialize with: python character_init.py")
        return 1

    if args.section:
        view_section(sheet, args.section)
    else:
        view_all(sheet)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
