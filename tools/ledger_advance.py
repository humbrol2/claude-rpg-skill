#!/usr/bin/env python3
"""Advance the ledger forward N days. Applies vehicle growth, realized inflows,
facility costs/revenues, and standing policies (liquid floor + auto-reinvest).

Usage: python ledger_advance.py --days N [--memory-dir PATH]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import find_memory_dir, load_ledger, save_ledger, fmt_money


def apply_vehicle_growth(ledger: dict, days: int) -> dict:
    """Compound each vehicle's valuation by weekly_unrealized_gain_pct."""
    weeks = days / 7
    deltas = {}
    for v in ledger.get("vehicles", []):
        pct = v.get("weekly_unrealized_gain_pct", 0)
        if pct == 0:
            continue
        before = v.get("valuation", 0)
        multiplier = (1 + pct / 100) ** weeks
        after = before * multiplier
        deltas[v["name"]] = after - before
        v["valuation"] = round(after, 4)
    return deltas


def apply_inflows(ledger: dict, days: int) -> float:
    """Add weekly_realized_inflows * (days/7) to liquid.operating."""
    weeks = days / 7
    total = 0.0
    for inflow in ledger.get("weekly_realized_inflows", []):
        amount = inflow.get("amount", 0) * weeks
        total += amount
    ledger.setdefault("liquid", {}).setdefault("operating", 0)
    ledger["liquid"]["operating"] = round(ledger["liquid"]["operating"] + total, 4)
    return total


def apply_facilities(ledger: dict, days: int) -> tuple[float, float]:
    """Apply weekly_operating_cost (subtract) and weekly_revenue (add) per facility."""
    weeks = days / 7
    total_cost = 0.0
    total_revenue = 0.0
    for fac in ledger.get("facilities", []):
        cost = fac.get("weekly_operating_cost", 0) * weeks
        rev = fac.get("weekly_revenue", 0) * weeks
        total_cost += cost
        total_revenue += rev
    ledger.setdefault("liquid", {}).setdefault("operating", 0)
    net = total_revenue - total_cost
    ledger["liquid"]["operating"] = round(ledger["liquid"]["operating"] + net, 4)
    return total_cost, total_revenue


def apply_liquid_floor_policy(ledger: dict) -> float:
    """If a liquid_floor policy exists, move excess from operating to realized_unredeployed."""
    policies = ledger.get("policies", [])
    has_floor = any(p.get("id") == "liquid_floor" for p in policies)
    if not has_floor:
        return 0.0

    liq = ledger.setdefault("liquid", {})
    operating = liq.setdefault("operating", 0)
    floor = liq.get("floor", 1.0)
    if operating <= floor:
        return 0.0

    excess = operating - floor
    liq["operating"] = floor
    liq["realized_unredeployed"] = round(liq.get("realized_unredeployed", 0) + excess, 4)
    return excess


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, required=True, help="Days to advance")
    ap.add_argument("--memory-dir", type=Path, default=None)
    ap.add_argument("--dry-run", action="store_true", help="Don't save changes")
    args = ap.parse_args()

    if args.days <= 0:
        print("--days must be positive")
        return 1

    memory_dir = args.memory_dir or find_memory_dir()
    ledger = load_ledger(memory_dir)
    if not ledger:
        print(f"No ledger found at {memory_dir}/economy/ledger.json")
        return 1

    as_of_before = ledger.get("as_of_day", 0)
    as_of_after = as_of_before + args.days

    vehicle_deltas = apply_vehicle_growth(ledger, args.days)
    inflows_total = apply_inflows(ledger, args.days)
    fac_cost, fac_rev = apply_facilities(ledger, args.days)
    excess_swept = apply_liquid_floor_policy(ledger)

    ledger["as_of_day"] = as_of_after
    ledger.setdefault("history", []).append({
        "day": as_of_after,
        "type": "advance",
        "delta_days": args.days,
        "inflows_total": round(inflows_total, 4),
        "facilities_cost": round(fac_cost, 4),
        "facilities_revenue": round(fac_rev, 4),
        "excess_swept_to_unredeployed": round(excess_swept, 4),
    })

    if not args.dry_run:
        save_ledger(memory_dir, ledger)

    print(f"Advanced {args.days} days. Day {as_of_before} → {as_of_after}.")
    print(f"  Realized inflows:    +{fmt_money(inflows_total)}")
    print(f"  Facilities net:      {fmt_money(fac_rev - fac_cost)}")
    print(f"  Excess swept to unredeployed: {fmt_money(excess_swept)}")
    print(f"  Vehicle growth (combined): +{fmt_money(sum(vehicle_deltas.values()))}")
    if args.dry_run:
        print("(dry run — not saved)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
