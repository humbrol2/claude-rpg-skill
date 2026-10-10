#!/usr/bin/env python3
"""The campaign ledger: the only source of truth for money.

Usage:
  python ledger.py show   [--memory-dir PATH]
  python ledger.py post   --delta N --note TEXT [--day D] [--denom NAME] [--actor WHO]
  python ledger.py tick   --days N [--note TEXT]
  python ledger.py set-day N

Ledger file: <memory>/economy/ledger.json
  as_of_day        integer in-fiction day
  currency         free text
  liquid           {denomination: amount}  (first denomination is the default)
  assets           list of strings (free form)
  monthly_inflows  [{source, amount, denom?}]
  monthly_outflows [{source, amount, denom?}]
  history          append-only [{day, type, delta, note, actor}]
Any other top-level keys (receivables, street_fund, ...) are campaign
extensions; `show` prints them verbatim and nothing here touches them.

`post` records one transaction and moves liquid in the same write — the
in-scene-payment rule. `tick` advances as_of_day and applies recurring
monthly flows prorated by days/30, one history line per flow.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import find_memory_dir, load_ledger, save_ledger  # noqa: E402

DAYS_PER_MONTH = 30  # the skill's calendar is 30-day months; prorate against it


def default_denom(ledger: dict) -> str:
    liquid = ledger.get("liquid") or {}
    if isinstance(liquid, dict) and liquid:
        return next(iter(liquid))
    return "cash"


def post(ledger: dict, delta: float, note: str, day: int | None, denom: str | None,
         actor: str, kind: str = "transaction") -> None:
    denom = denom or default_denom(ledger)
    liquid = ledger.setdefault("liquid", {})
    if not isinstance(liquid, dict):
        raise SystemExit("ledger.liquid is not a {denomination: amount} map; fix the file first")
    before = liquid.get(denom, 0)
    after = round(before + delta, 2)
    liquid[denom] = int(after) if float(after).is_integer() else after
    ledger.setdefault("history", []).append({
        "day": day if day is not None else ledger.get("as_of_day", 0),
        "type": kind,
        "delta": f"{'+' if delta >= 0 else ''}{delta:g} {denom}",
        "note": note,
        "actor": actor,
    })


def tick(ledger: dict, days: int, note: str) -> list[str]:
    start = int(ledger.get("as_of_day", 0))
    end = start + days
    lines = [f"Day {start} -> {end} ({days} days)"]
    factor = days / DAYS_PER_MONTH
    for sign, key in ((+1, "monthly_inflows"), (-1, "monthly_outflows")):
        for flow in ledger.get(key, []) or []:
            if not isinstance(flow, dict):
                lines.append(f"  (manual) {flow} — free-text flow, post it by hand")
                continue
            amount = round(sign * float(flow.get("amount", 0)) * factor, 2)
            if amount == 0:
                continue
            post(ledger, amount, f"{flow.get('source', key)} ({days}d of monthly)",
                 end, flow.get("denom"), "ledger.tick", kind="recurring")
            lines.append(f"  {amount:+g} {flow.get('denom') or default_denom(ledger)}  {flow.get('source', key)}")
    ledger["as_of_day"] = end
    ledger.setdefault("history", []).append(
        {"day": end, "type": "tick", "delta": f"+{days} days", "note": note or "time advanced", "actor": "ledger.tick"})
    return lines


def show(ledger: dict) -> str:
    if not ledger:
        return "No ledger. Run `ledger.py post` after confirming starting liquid with the player, or create economy/ledger.json."
    out = [f"Day {ledger.get('as_of_day', '?')}"]
    liquid = ledger.get("liquid", {})
    out.append("Liquid: " + (", ".join(f"{v} {k}" for k, v in liquid.items()) if isinstance(liquid, dict) else str(liquid)))
    for key in ("monthly_inflows", "monthly_outflows"):
        flows = ledger.get(key) or []
        if flows:
            # Flows may be structured ({source, amount}) or free-text strings
            # written by hand during play; show both as written.
            out.append(f"{key.replace('_', ' ').title()}: " + "; ".join(
                f"{f.get('source', '?')} {f.get('amount', 0):g}" if isinstance(f, dict) else str(f)
                for f in flows))
    standard = {"as_of_day", "currency", "liquid", "assets", "monthly_inflows", "monthly_outflows", "history"}
    for key, val in ledger.items():
        if key not in standard:
            out.append(f"{key}: {json.dumps(val, ensure_ascii=False)}")
    assets = ledger.get("assets") or []
    if assets:
        out.append(f"Assets ({len(assets)}): " + "; ".join(str(a) for a in assets[:8]) + (" …" if len(assets) > 8 else ""))
    hist = ledger.get("history") or []
    if hist:
        out.append("Recent:")
        for h in hist[-5:]:
            out.append(f"  Day {h.get('day', '?')}: {h.get('delta', '')}  {h.get('note', h.get('type', ''))}")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--memory-dir", type=Path, default=None)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("show")
    p = sub.add_parser("post")
    p.add_argument("--delta", type=float, required=True, help="negative for spend")
    p.add_argument("--note", required=True)
    p.add_argument("--day", type=int, default=None)
    p.add_argument("--denom", default=None)
    p.add_argument("--actor", default="narrator")
    t = sub.add_parser("tick")
    t.add_argument("--days", type=int, required=True)
    t.add_argument("--note", default="")
    s = sub.add_parser("set-day")
    s.add_argument("day", type=int)
    args = ap.parse_args()

    memory_dir = args.memory_dir or find_memory_dir()
    ledger = load_ledger(memory_dir)

    if args.cmd == "show":
        print(show(ledger))
        return 0
    if args.cmd == "post":
        post(ledger, args.delta, args.note, args.day, args.denom, args.actor)
    elif args.cmd == "tick":
        if args.days < 1 or args.days > 7:
            print("error: tick is 1–7 days (the skill's hard ceiling per response)", file=sys.stderr)
            return 2
        print("\n".join(tick(ledger, args.days, args.note)))
    elif args.cmd == "set-day":
        ledger["as_of_day"] = args.day
    save_ledger(memory_dir, ledger)
    print(show(ledger))
    return 0


if __name__ == "__main__":
    sys.exit(main())
