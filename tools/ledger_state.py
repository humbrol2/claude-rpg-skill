#!/usr/bin/env python3
"""Print the current ledger state in tight RPG-format.

Usage: python ledger_state.py [--memory-dir PATH] [--verbose]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import find_memory_dir, load_ledger, fmt_money


def compute_weekly_realized(ledger: dict) -> float:
    return sum(item.get("amount", 0) for item in ledger.get("weekly_realized_inflows", []))


def compute_weekly_unrealized(ledger: dict) -> float:
    total = 0.0
    for v in ledger.get("vehicles", []):
        pct = v.get("weekly_unrealized_gain_pct", 0)
        total += v.get("valuation", 0) * pct / 100
    return total


def compute_total_liquid(ledger: dict) -> float:
    liq = ledger.get("liquid", {})
    return liq.get("operating", 0) + liq.get("off_books", 0) + liq.get("realized_unredeployed", 0)


def compute_total_unrealized_valuation(ledger: dict) -> float:
    return sum(v.get("valuation", 0) for v in ledger.get("vehicles", []))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--memory-dir", type=Path, default=None)
    ap.add_argument("--verbose", action="store_true", help="Show full vehicle breakdown")
    args = ap.parse_args()

    memory_dir = args.memory_dir or find_memory_dir()
    ledger = load_ledger(memory_dir)

    if not ledger:
        print(f"No ledger found at {memory_dir}/economy/ledger.json")
        print("Initialize with: python ledger_init.py")
        return 1

    as_of = ledger.get("as_of_day", "?")
    liquid = compute_total_liquid(ledger)
    weekly_realized = compute_weekly_realized(ledger)
    weekly_unrealized = compute_weekly_unrealized(ledger)
    weekly_combined = weekly_realized + weekly_unrealized
    total_unrealized = compute_total_unrealized_valuation(ledger)

    print(f"As of Day {as_of}:")
    print(f"  Liquid cash:        {fmt_money(liquid)}")
    print(f"  Weekly realized:    {fmt_money(weekly_realized)}")
    print(f"  Weekly unrealized:  {fmt_money(weekly_unrealized)}")
    print(f"  Weekly combined:    {fmt_money(weekly_combined)}")
    print(f"  Total unrealized:   {fmt_money(total_unrealized)}")

    if args.verbose:
        print()
        print("Liquid breakdown:")
        for k, v in ledger.get("liquid", {}).items():
            print(f"  {k:25s} {fmt_money(v)}")
        print()
        print("Vehicles:")
        for v in ledger.get("vehicles", []):
            name = v.get("name", "<unnamed>")
            deployed = v.get("deployed", 0)
            valuation = v.get("valuation", 0)
            pct = v.get("weekly_unrealized_gain_pct", 0)
            print(f"  {name:35s} deployed {fmt_money(deployed):>10s}  val {fmt_money(valuation):>10s}  @{pct:.2f}%/wk")
        print()
        print("Realized inflows:")
        for inflow in ledger.get("weekly_realized_inflows", []):
            print(f"  {inflow.get('source', '<unnamed>'):35s} {fmt_money(inflow.get('amount', 0)):>10s}/wk")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
