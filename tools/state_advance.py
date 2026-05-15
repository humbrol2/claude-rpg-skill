#!/usr/bin/env python3
"""Advance research projects, fleet self-replication, and construction sites by N days.

Updates research.json, fleet.json, locations.json based on rates encoded in each file.

Usage: python state_advance.py --days N [--memory-dir PATH] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import find_memory_dir


def load_state(memory_dir: Path, name: str) -> dict:
    path = memory_dir / "state" / name
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(memory_dir: Path, name: str, state: dict) -> None:
    path = memory_dir / "state" / name
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    tmp.replace(path)


def advance_research(state: dict, days: int) -> list[str]:
    """Advance project progress percentages by their daily rates. Mark milestones if reached."""
    if not state:
        return []
    messages = []
    current_day = state.get("as_of_day", 0)
    new_day = current_day + days

    for project in state.get("active_projects", []):
        rate = project.get("daily_progress_pct", 0)
        if rate > 0:
            old_progress = project.get("progress_pct", 0)
            new_progress = min(100, old_progress + rate * days)
            project["progress_pct"] = round(new_progress, 2)
            if new_progress >= 100 and old_progress < 100:
                messages.append(f"  PROJECT COMPLETE: {project.get('name')}")

    for milestone in state.get("milestones", []):
        target = milestone.get("target_day", 0)
        if not milestone.get("achieved") and current_day < target <= new_day:
            milestone["achieved"] = True
            milestone["achieved_day"] = target
            messages.append(f"  MILESTONE: {milestone.get('description')} (Day {target})")

    state["as_of_day"] = new_day
    state.setdefault("history", []).append({"day": new_day, "type": "advance", "delta_days": days})
    return messages


def advance_fleet(state: dict, days: int) -> list[str]:
    """Advance droid self-replication if a rate is encoded."""
    if not state:
        return []
    messages = []
    current_day = state.get("as_of_day", 0)
    new_day = current_day + days

    droids = state.get("droids", {})
    weekly_production = droids.get("weekly_production_rate", 0)
    if weekly_production > 0:
        increment = round(weekly_production * days / 7)
        if increment > 0:
            droids["total"] = droids.get("total", 0) + increment
            messages.append(f"  Droids +{increment} (rate {weekly_production}/wk × {days}d)")
            default_loc = droids.get("default_production_location", "primary_base")
            by_location = droids.setdefault("by_location", {})
            by_location[default_loc] = by_location.get(default_loc, 0) + increment

    state["as_of_day"] = new_day
    state.setdefault("history", []).append({"day": new_day, "type": "advance", "delta_days": days})
    return messages


def advance_locations(state: dict, days: int) -> list[str]:
    """Advance construction site completion percentages."""
    if not state:
        return []
    messages = []
    current_day = state.get("as_of_day", 0)
    new_day = current_day + days

    for site in state.get("construction_sites", []):
        rate = site.get("daily_progress_pct", 0)
        if rate > 0:
            old = site.get("completion_pct", 0)
            new = min(100, old + rate * days)
            site["completion_pct"] = round(new, 2)
            if new >= 100 and old < 100:
                messages.append(f"  CONSTRUCTION COMPLETE: {site.get('name')}")

    state["as_of_day"] = new_day
    state.setdefault("history", []).append({"day": new_day, "type": "advance", "delta_days": days})
    return messages


def advance_threads(state: dict, days: int) -> list[str]:
    """Tick threads forward. Surface any whose next_anchor_day has been reached."""
    if not state:
        return []
    messages = []
    current_day = state.get("as_of_day", 0)
    new_day = current_day + days

    for thread in state.get("open_threads", []):
        anchor = thread.get("next_anchor_day")
        if anchor and current_day < anchor <= new_day:
            messages.append(f"  THREAD ANCHOR: {thread.get('name')} (Day {anchor}) — surface in narration")

    state["as_of_day"] = new_day
    state.setdefault("history", []).append({"day": new_day, "type": "advance", "delta_days": days})
    return messages


def advance_simple(state: dict, days: int) -> None:
    """Just stamp the day forward for files without specific tick logic."""
    if not state:
        return
    current_day = state.get("as_of_day", 0)
    state["as_of_day"] = current_day + days
    state.setdefault("history", []).append({"day": state["as_of_day"], "type": "advance", "delta_days": days})


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, required=True)
    ap.add_argument("--memory-dir", type=Path, default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    memory_dir = args.memory_dir or find_memory_dir()

    all_messages = []

    research = load_state(memory_dir, "research.json")
    fleet = load_state(memory_dir, "fleet.json")
    locations = load_state(memory_dir, "locations.json")
    threads = load_state(memory_dir, "threads.json")
    cover = load_state(memory_dir, "cover.json")
    secrecy = load_state(memory_dir, "secrecy.json")
    character = load_state(memory_dir, "character.json")

    all_messages.extend(advance_research(research, args.days))
    all_messages.extend(advance_fleet(fleet, args.days))
    all_messages.extend(advance_locations(locations, args.days))
    all_messages.extend(advance_threads(threads, args.days))
    advance_simple(cover, args.days)
    advance_simple(secrecy, args.days)
    advance_simple(character, args.days)

    if not args.dry_run:
        if research:
            save_state(memory_dir, "research.json", research)
        if fleet:
            save_state(memory_dir, "fleet.json", fleet)
        if locations:
            save_state(memory_dir, "locations.json", locations)
        if threads:
            save_state(memory_dir, "threads.json", threads)
        if cover:
            save_state(memory_dir, "cover.json", cover)
        if secrecy:
            save_state(memory_dir, "secrecy.json", secrecy)
        if character:
            save_state(memory_dir, "character.json", character)

    print(f"Advanced {args.days} days.")
    if all_messages:
        print("Events:")
        for m in all_messages:
            print(m)
    else:
        print("  (no completions, milestones, or production events this window)")
    if args.dry_run:
        print("(dry run — not saved)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
