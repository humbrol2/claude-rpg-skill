#!/usr/bin/env python3
"""Record a deployment to a vehicle. Pulls from liquid; adds to vehicle deployed + valuation.

Usage: python ledger_deploy.py --amount 5 --vehicle "Threll-Vor Capital" [--source operating|off_books|realized_unredeployed|auto]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import find_memory_dir, load_ledger, save_ledger, fmt_money


def find_vehicle(ledger: dict, name: str) -> dict | None:
    for v in ledger.get("vehicles", []):
        if v.get("name", "").lower() == name.lower():
            return v
    return None


def pull_from_liquid(ledger: dict, amount: float, source: str) -> tuple[float, list[str]]:
    """Withdraw amount from liquid sources. Returns (amount_pulled, messages).

    If source=='auto', pulls in order: realized_unredeployed, off_books, operating.
    """
    liq = ledger.setdefault("liquid", {})
    operating = liq.setdefault("operating", 0)
    off_books = liq.setdefault("off_books", 0)
    realized_unredeployed = liq.setdefault("realized_unredeployed", 0)

    messages = []
    remaining = amount
    pulled = 0.0

    sources_in_order = (
        ["realized_unredeployed", "off_books", "operating"]
        if source == "auto"
        else [source]
    )

    for src in sources_in_order:
        if remaining <= 0:
            break
        available = liq.get(src, 0)
        if available <= 0:
            continue
        take = min(available, remaining)
        liq[src] = round(available - take, 4)
        pulled += take
        remaining -= take
        messages.append(f"  pulled {fmt_money(take)} from {src}")

    if remaining > 0:
        messages.append(f"  WARNING: insufficient liquid; short by {fmt_money(remaining)}")
    return pulled, messages


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--amount", type=float, required=True, help="Amount in M_cr")
    ap.add_argument("--vehicle", type=str, required=True)
    ap.add_argument("--source", type=str, default="auto",
                    choices=["operating", "off_books", "realized_unredeployed", "auto"])
    ap.add_argument("--memory-dir", type=Path, default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    memory_dir = args.memory_dir or find_memory_dir()
    ledger = load_ledger(memory_dir)
    if not ledger:
        print(f"No ledger at {memory_dir}/economy/ledger.json")
        return 1

    vehicle = find_vehicle(ledger, args.vehicle)
    if not vehicle:
        print(f"Vehicle '{args.vehicle}' not found. Available:")
        for v in ledger.get("vehicles", []):
            print(f"  - {v.get('name')}")
        return 1

    pulled, msgs = pull_from_liquid(ledger, args.amount, args.source)
    vehicle["deployed"] = round(vehicle.get("deployed", 0) + pulled, 4)
    vehicle["valuation"] = round(vehicle.get("valuation", 0) + pulled, 4)

    ledger.setdefault("history", []).append({
        "day": ledger.get("as_of_day", "?"),
        "type": "deployment",
        "amount": round(pulled, 4),
        "vehicle": vehicle["name"],
        "source": args.source,
    })

    if not args.dry_run:
        save_ledger(memory_dir, ledger)

    print(f"Deployed {fmt_money(pulled)} to {vehicle['name']}.")
    for m in msgs:
        print(m)
    print(f"  Vehicle now: deployed {fmt_money(vehicle['deployed'])}, valuation {fmt_money(vehicle['valuation'])}")
    if args.dry_run:
        print("(dry run — not saved)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
