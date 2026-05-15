#!/usr/bin/env python3
"""Initialize empty state files (research, fleet, locations) at memory_dir/state/.

Usage: python state_init.py [--memory-dir PATH] [--day N] [--force]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import find_memory_dir


def init_file(state_dir: Path, name: str, schema: dict, force: bool) -> bool:
    path = state_dir / name
    if path.exists() and not force:
        print(f"  exists, skipped: {path} (use --force to overwrite)")
        return False
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)
    tmp.replace(path)
    print(f"  initialized: {path}")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--memory-dir", type=Path, default=None)
    ap.add_argument("--day", type=int, default=0)
    ap.add_argument("--year", type=str, default="", help="Calendar year designator (e.g., 'ASC 1487')")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    memory_dir = args.memory_dir or find_memory_dir()
    state_dir = memory_dir / "state"
    state_dir.mkdir(parents=True, exist_ok=True)

    research_schema = {
        "as_of_day": args.day,
        "as_of_year": args.year,
        "compute": {
            "substrate_baseline_multiplier": 1.0,
            "substrate_generations_active": ["v1"],
            "notes": "Compute substrate technology generation(s) currently in service"
        },
        "domains": [],
        "active_projects": [],
        "milestones": [],
        "capability_stack": [],
        "history": [{"day": args.day, "type": "init"}]
    }

    fleet_schema = {
        "as_of_day": args.day,
        "as_of_year": args.year,
        "ships": [],
        "drones": [],
        "droids": {
            "by_location": {},
            "by_generation": {},
            "total": 0,
            "notes": "Humanoid droid fleet — count by location and generation"
        },
        "history": [{"day": args.day, "type": "init"}]
    }

    locations_schema = {
        "as_of_day": args.day,
        "as_of_year": args.year,
        "bases": [],
        "stations": [],
        "construction_sites": [],
        "history": [{"day": args.day, "type": "init"}]
    }

    threads_schema = {
        "as_of_day": args.day,
        "as_of_year": args.year,
        "open_threads": [],
        "resolved_threads": [],
        "notes": "Open narrative threads / arcs in motion. Each thread carries name, status, pace, next_anchor_day, and brief context. Check before time-skipping to identify threads that need attention.",
        "history": [{"day": args.day, "type": "init"}]
    }

    cover_schema = {
        "as_of_day": args.day,
        "as_of_year": args.year,
        "primary_identity": "",
        "active_covers": [],
        "retired_covers": [],
        "notes": "Cover identities the PC uses in different contexts. Each carries name, context (where used), first_used day, status, and any known compromise risk.",
        "history": [{"day": args.day, "type": "init"}]
    }

    secrecy_schema = {
        "as_of_day": args.day,
        "as_of_year": args.year,
        "inner_circle": [],
        "outer_circle_default": True,
        "partial_read_in": [],
        "notes": "Who knows what. inner_circle: full read-in. partial_read_in: specific topics. Everyone else is outer-circle (cover narrative only).",
        "history": [{"day": args.day, "type": "init"}]
    }

    print(f"Initializing state files at {state_dir}/")
    init_file(state_dir, "research.json", research_schema, args.force)
    init_file(state_dir, "fleet.json", fleet_schema, args.force)
    init_file(state_dir, "locations.json", locations_schema, args.force)
    init_file(state_dir, "threads.json", threads_schema, args.force)
    init_file(state_dir, "cover.json", cover_schema, args.force)
    init_file(state_dir, "secrecy.json", secrecy_schema, args.force)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
