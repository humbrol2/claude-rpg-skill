#!/usr/bin/env python3
"""Initialize a PC character sheet at memory_dir/state/character.json.

Schema covers true name + cover identities, heritage standings, skills/attributes,
possessions, core relationships, goals, and history anchors.

Usage: python character_init.py --memory-dir PATH [--true-name NAME] [--day N] [--force]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import find_memory_dir


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--memory-dir", type=Path, default=None)
    ap.add_argument("--true-name", type=str, default="")
    ap.add_argument("--day", type=int, default=0)
    ap.add_argument("--year", type=str, default="")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    memory_dir = args.memory_dir or find_memory_dir()
    state_dir = memory_dir / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    path = state_dir / "character.json"

    if path.exists() and not args.force:
        print(f"Character sheet exists at {path}. Use --force to overwrite.")
        return 1

    schema = {
        "as_of_day": args.day,
        "as_of_year": args.year,
        "true_name": args.true_name,
        "pronouns": "",
        "species": "",
        "age": "",
        "physical_description": "",
        "cover_identities": [],
        "heritage_standings": [],
        "attributes": {},
        "skills": {},
        "possessions": [],
        "personal_items_carried": [],
        "core_relationships": [],
        "goals": {
            "near_term": [],
            "medium_term": [],
            "long_term": []
        },
        "history_anchors": [],
        "notes": "Character sheet for the player character. Update as the character develops.",
        "history": [{"day": args.day, "type": "init"}]
    }

    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)
    tmp.replace(path)

    print(f"Initialized character sheet at {path}")
    print("Next: edit the JSON directly or use character_view.py to inspect / character_update.py to add entries.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
