#!/usr/bin/env python3
"""Initialize a fresh ledger at memory_dir/economy/ledger.json.

Usage: python ledger_init.py [--memory-dir PATH] [--day N]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import find_memory_dir, save_ledger


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--memory-dir", type=Path, default=None)
    ap.add_argument("--day", type=int, default=0, help="Starting ASC day")
    ap.add_argument("--force", action="store_true", help="Overwrite existing ledger")
    args = ap.parse_args()

    memory_dir = args.memory_dir or find_memory_dir()
    ledger_path = memory_dir / "economy" / "ledger.json"

    if ledger_path.exists() and not args.force:
        print(f"Ledger already exists at {ledger_path}")
        print("Use --force to overwrite (will destroy existing state).")
        return 1

    starter: dict = {
        "as_of_day": args.day,
        "currency": "M_cr",
        "liquid": {
            "operating": 0.0,
            "off_books": 0.0,
            "realized_unredeployed": 0.0,
            "floor": 1.0,
        },
        "vehicles": [],
        "facilities": [],
        "weekly_realized_inflows": [],
        "policies": [],
        "history": [
            {"day": args.day, "type": "init", "note": "ledger initialized"},
        ],
    }

    save_ledger(memory_dir, starter)
    print(f"Initialized ledger at {ledger_path}")
    print("Next steps:")
    print("  Add vehicles, facilities, inflows manually or via deploy commands.")
    print("  Set policies (e.g., liquid_floor) in the JSON directly.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
