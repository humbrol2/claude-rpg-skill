#!/usr/bin/env python3
"""Session tracking: beats, threads, pressures, and the one-screen status.

Usage:
  python track.py status                      day, liquid, hot threads, high pressures, last beats
  python track.py threads  [--all]            threads by status; STALE = 100+ days unadvanced
  python track.py pressures [--all]           unresolved pressures by urgency
  python track.py beat --day N --type T --summary S [--thread ID ...]
  python track.py thread-add --id ID --title T [--status HOT] [--day N]
  python track.py thread-set --id ID [--status S] [--day N]
  python track.py pressure-add --id ID --title T --urgency HIGH|MED|LOW [--due N]
  python track.py pressure-resolve --id ID

Files (all under <memory>/):
  sessions/beat_log.json   [{day, type, summary}]
  sessions/threads.json    [{id, title, status, opened_day, last_advanced_day}]
  economy/pressures.json   [{id, title, urgency, due_day, resolved}]
Missing files are created on first write. `beat --thread` bumps those
threads' last_advanced_day in the same write, so logging a beat and
advancing its threads cannot drift apart.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import find_memory_dir, load_ledger  # noqa: E402

STALE_AFTER_DAYS = 100   # SKILL.md: a thread unadvanced this long is flagged STALE at boot
DUE_SOON_DAYS = 30       # SKILL.md: pressures due within this window surface at boot
STATUS_ORDER = {"HOT": 0, "WARM": 1, "COOL": 2, "STALE": 3, "CLOSED": 4}
TITLE_CHARS = 120        # thread titles accrete whole histories in play; status shows the head only
STATUS_STALE_SHOWN = 3   # status names the 3 most recently idle STALE threads and counts the rest


def head(text: object, n: int = TITLE_CHARS) -> str:
    s = str(text)
    return s if len(s) <= n else s[:n].rstrip() + " …"


def load_list(path: Path) -> list:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{path} is not valid JSON ({exc}); fix it before writing")
    return data if isinstance(data, list) else []


def save_list(path: Path, data: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


def current_day(memory_dir: Path, beats: list) -> int:
    ledger = load_ledger(memory_dir)
    if ledger.get("as_of_day") is not None:
        return int(ledger["as_of_day"])
    return int(beats[-1]["day"]) if beats else 0


def effective_status(t: dict, today: int) -> str:
    status = str(t.get("status", "WARM")).upper()
    if status != "CLOSED" and today - int(t.get("last_advanced_day", today)) >= STALE_AFTER_DAYS:
        return "STALE"
    return status


def fmt_threads(threads: list, today: int, show_all: bool) -> str:
    rows = []
    for t in threads:
        st = effective_status(t, today)
        if st == "CLOSED" and not show_all:
            continue
        idle = today - int(t.get("last_advanced_day", today))
        rows.append((STATUS_ORDER.get(st, 9), idle, f"  [{st}] {t.get('id')}: {head(t.get('title'))} (idle {idle}d)"))
    if not rows:
        return "No open threads."
    rows.sort(key=lambda r: (r[0], -r[1]))
    return "\n".join(r[2] for r in rows)


def fmt_pressures(pressures: list, today: int, show_all: bool) -> str:
    order = {"HIGH": 0, "MED": 1, "MEDIUM": 1, "LOW": 2}
    rows = []
    for p in pressures:
        if p.get("resolved") and not show_all:
            continue
        due = p.get("due_day")
        due_s = f", due day {due}" if due is not None else ""
        soon = " DUE SOON" if due is not None and 0 <= int(due) - today <= DUE_SOON_DAYS else ""
        urg = str(p.get("urgency", "LOW")).upper()
        rows.append((order.get(urg, 3), f"  [{urg}] {p.get('id')}: {head(p.get('title'))}{due_s}{soon}"))
    if not rows:
        return "No unresolved pressures."
    rows.sort(key=lambda r: r[0])
    return "\n".join(r[1] for r in rows)


def status_text(memory_dir: Path) -> str:
    beats = load_list(memory_dir / "sessions" / "beat_log.json")
    threads = load_list(memory_dir / "sessions" / "threads.json")
    pressures = load_list(memory_dir / "economy" / "pressures.json")
    today = current_day(memory_dir, beats)
    ledger = load_ledger(memory_dir)
    liquid = ledger.get("liquid", {})
    liq = ", ".join(f"{v} {k}" for k, v in liquid.items()) if isinstance(liquid, dict) and liquid else "no ledger"
    out = [f"Day {today}. Liquid: {liq}."]
    hot = [t for t in threads if effective_status(t, today) == "HOT"]
    stale = sorted((t for t in threads if effective_status(t, today) == "STALE"),
                   key=lambda t: -int(t.get("last_advanced_day", 0)))
    if hot:
        out.append("HOT threads:")
        out.append(fmt_threads(hot, today, False))
    if stale:
        out.append(f"STALE threads: {len(stale)} (100+ days idle; `track.py threads` lists all). Most recent:")
        out.append(fmt_threads(stale[:STATUS_STALE_SHOWN], today, False))
    open_p = [p for p in pressures if not p.get("resolved")]
    due_soon = [p for p in open_p if p.get("due_day") is not None and 0 <= int(p["due_day"]) - today <= DUE_SOON_DAYS]
    high = [p for p in open_p if str(p.get("urgency", "")).upper() == "HIGH" and p not in due_soon]
    if due_soon:
        out.append("Pressures due soon:")
        out.append(fmt_pressures(due_soon, today, False))
    if high:
        # HIGH accretes in long campaigns (Pride II: 24 open HIGH with no due day);
        # status shows the newest few and counts the rest.
        out.append(f"HIGH pressures: {len(high)} open (`track.py pressures` lists all). Newest:")
        out.append(fmt_pressures(high[-STATUS_STALE_SHOWN:], today, False))
    if beats:
        out.append("Last beats:")
        for b in beats[-5:]:
            out.append(f"  Day {b.get('day', '?')} [{b.get('type', '?')}] {b.get('summary', '')}")
        types = [b.get("type") for b in beats[-3:]]
        if len(types) == 3 and len(set(types)) == 1:
            out.append(f"  VARIETY FLAG: last 3 beats all '{types[0]}' — vary the next beat.")
        elif len(types) == 3 and max(types.count(x) for x in set(types)) >= 2:
            out.append(f"  Variety note: 2 of last 3 beats are '{max(set(types), key=types.count)}'.")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--memory-dir", type=Path, default=None)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    for name in ("threads", "pressures"):
        sub.add_parser(name).add_argument("--all", action="store_true")
    b = sub.add_parser("beat")
    b.add_argument("--day", type=int, required=True)
    b.add_argument("--type", required=True)
    b.add_argument("--summary", required=True)
    b.add_argument("--thread", action="append", default=[], help="thread id advanced by this beat")
    ta = sub.add_parser("thread-add")
    ta.add_argument("--id", required=True)
    ta.add_argument("--title", required=True)
    ta.add_argument("--status", default="HOT")
    ta.add_argument("--day", type=int, default=None)
    ts = sub.add_parser("thread-set")
    ts.add_argument("--id", required=True)
    ts.add_argument("--status", default=None)
    ts.add_argument("--day", type=int, default=None)
    pa = sub.add_parser("pressure-add")
    pa.add_argument("--id", required=True)
    pa.add_argument("--title", required=True)
    pa.add_argument("--urgency", required=True, choices=["HIGH", "MED", "LOW"])
    pa.add_argument("--due", type=int, default=None)
    pr = sub.add_parser("pressure-resolve")
    pr.add_argument("--id", required=True)
    args = ap.parse_args()

    memory_dir = args.memory_dir or find_memory_dir()
    beats_path = memory_dir / "sessions" / "beat_log.json"
    threads_path = memory_dir / "sessions" / "threads.json"
    pressures_path = memory_dir / "economy" / "pressures.json"
    beats = load_list(beats_path)
    threads = load_list(threads_path)
    pressures = load_list(pressures_path)
    today = current_day(memory_dir, beats)

    if args.cmd == "status":
        print(status_text(memory_dir))
    elif args.cmd == "threads":
        print(fmt_threads(threads, today, args.all))
    elif args.cmd == "pressures":
        print(fmt_pressures(pressures, today, args.all))
    elif args.cmd == "beat":
        beats.append({"day": args.day, "type": args.type, "summary": args.summary})
        save_list(beats_path, beats)
        missing = []
        for tid in args.thread:
            hit = next((t for t in threads if t.get("id") == tid), None)
            if hit is None:
                missing.append(tid)
            else:
                hit["last_advanced_day"] = max(int(hit.get("last_advanced_day", 0)), args.day)
        if args.thread:
            save_list(threads_path, threads)
        print(f"Beat logged (Day {args.day}, {args.type}). {len(beats)} beats total.")
        if missing:
            print(f"warning: unknown thread id(s) {missing} — add with thread-add first")
    elif args.cmd == "thread-add":
        if any(t.get("id") == args.id for t in threads):
            raise SystemExit(f"thread {args.id!r} already exists; use thread-set")
        day = args.day if args.day is not None else today
        threads.append({"id": args.id, "title": args.title, "status": args.status.upper(),
                        "opened_day": day, "last_advanced_day": day})
        save_list(threads_path, threads)
        print(f"Thread added: {args.id}")
    elif args.cmd == "thread-set":
        hit = next((t for t in threads if t.get("id") == args.id), None)
        if hit is None:
            raise SystemExit(f"no thread {args.id!r}")
        if args.status:
            hit["status"] = args.status.upper()
        if args.day is not None:
            hit["last_advanced_day"] = args.day
        save_list(threads_path, threads)
        print(f"Thread updated: {args.id} [{hit['status']}] last advanced day {hit.get('last_advanced_day')}")
    elif args.cmd == "pressure-add":
        if any(p.get("id") == args.id for p in pressures):
            raise SystemExit(f"pressure {args.id!r} already exists")
        pressures.append({"id": args.id, "title": args.title, "urgency": args.urgency,
                          "due_day": args.due, "resolved": False})
        save_list(pressures_path, pressures)
        print(f"Pressure added: {args.id} [{args.urgency}]")
    elif args.cmd == "pressure-resolve":
        hit = next((p for p in pressures if p.get("id") == args.id), None)
        if hit is None:
            raise SystemExit(f"no pressure {args.id!r}")
        hit["resolved"] = True
        save_list(pressures_path, pressures)
        print(f"Pressure resolved: {args.id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
