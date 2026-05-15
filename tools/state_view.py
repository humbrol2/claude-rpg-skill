#!/usr/bin/env python3
"""Print a tight summary of research / fleet / locations state.

Usage: python state_view.py [--what research|fleet|locations|all] [--memory-dir PATH]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import find_memory_dir


def load(memory_dir: Path, name: str) -> dict:
    path = memory_dir / "state" / name
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def view_research(memory_dir: Path) -> None:
    state = load(memory_dir, "research.json")
    if not state:
        print("(research.json missing — run state_init.py)")
        return

    print(f"=== Research (Day {state.get('as_of_day', '?')}) ===")
    compute = state.get("compute", {})
    mult = compute.get("substrate_baseline_multiplier", 1)
    gens = ", ".join(compute.get("substrate_generations_active", []))
    print(f"  Compute: {mult}x baseline ({gens})")

    domains = state.get("domains", [])
    if domains:
        print(f"  Domains active: {len(domains)}")
        for d in domains:
            name = d.get("name", "<unnamed>")
            focus = d.get("focus", "")
            alloc = d.get("allocation_pct", 0)
            print(f"    [{alloc:4.1f}%] {name}: {focus}")

    projects = state.get("active_projects", [])
    if projects:
        print(f"  Active projects: {len(projects)}")
        for p in projects:
            name = p.get("name", "<unnamed>")
            progress = p.get("progress_pct", 0)
            eta_day = p.get("eta_day", "?")
            print(f"    [{progress:3.0f}%] {name} (ETA Day {eta_day})")

    milestones = state.get("milestones", [])
    if milestones:
        upcoming = [m for m in milestones if not m.get("achieved", False)]
        if upcoming:
            print(f"  Upcoming milestones: {len(upcoming)}")
            for m in upcoming[:5]:
                print(f"    Day {m.get('target_day', '?')}: {m.get('description', '')}")

    cap = state.get("capability_stack", [])
    if cap:
        print(f"  Capabilities ({len(cap)}):")
        for c in cap:
            print(f"    - {c.get('name', '<unnamed>')}: {c.get('status', '')}")


def view_fleet(memory_dir: Path) -> None:
    state = load(memory_dir, "fleet.json")
    if not state:
        print("(fleet.json missing — run state_init.py)")
        return

    print(f"=== Fleet (Day {state.get('as_of_day', '?')}) ===")
    droids = state.get("droids", {})
    if droids.get("total"):
        print(f"  Droids total: {droids['total']}")
        for loc, n in droids.get("by_location", {}).items():
            print(f"    {loc}: {n}")
        for gen, n in droids.get("by_generation", {}).items():
            print(f"    [{gen}]: {n}")

    ships = state.get("ships", [])
    if ships:
        print(f"  Ships: {len(ships)}")
        for s in ships:
            name = s.get("name", "<unnamed>")
            cls = s.get("class", "")
            status = s.get("status", "")
            location = s.get("location", "")
            print(f"    {name} ({cls}) — {status} at {location}")

    drones = state.get("drones", [])
    if drones:
        print(f"  Drones / deployed platforms: {len(drones)} groups")
        for d in drones:
            name = d.get("name", "<unnamed>")
            count = d.get("count", 1)
            mission = d.get("mission", "")
            print(f"    {count}x {name}: {mission}")


def view_locations(memory_dir: Path) -> None:
    state = load(memory_dir, "locations.json")
    if not state:
        print("(locations.json missing — run state_init.py)")
        return

    print(f"=== Locations (Day {state.get('as_of_day', '?')}) ===")
    for category in ("bases", "stations", "construction_sites"):
        items = state.get(category, [])
        if items:
            print(f"  {category.title()}: {len(items)}")
            for loc in items:
                name = loc.get("name", "<unnamed>")
                status = loc.get("status", "")
                notes = loc.get("notes", "")
                print(f"    {name} — {status}" + (f" — {notes}" if notes else ""))


def view_threads(memory_dir: Path) -> None:
    state = load(memory_dir, "threads.json")
    if not state:
        print("(threads.json missing — run state_init.py)")
        return

    print(f"=== Threads (Day {state.get('as_of_day', '?')}) ===")
    open_threads = state.get("open_threads", [])
    if open_threads:
        print(f"  Open threads: {len(open_threads)}")
        for t in open_threads:
            name = t.get("name", "<unnamed>")
            status = t.get("status", "")
            pace = t.get("pace", "")
            anchor = t.get("next_anchor_day", "?")
            print(f"    [{status:8s}] {name} (pace: {pace}, next anchor Day {anchor})")
    resolved = state.get("resolved_threads", [])
    if resolved:
        print(f"  Resolved: {len(resolved)}")


def view_cover(memory_dir: Path) -> None:
    state = load(memory_dir, "cover.json")
    if not state:
        print("(cover.json missing — run state_init.py)")
        return

    print(f"=== Cover identities (Day {state.get('as_of_day', '?')}) ===")
    print(f"  Primary identity: {state.get('primary_identity', '<unset>')}")
    active = state.get("active_covers", [])
    if active:
        print(f"  Active covers: {len(active)}")
        for c in active:
            name = c.get("name", "<unnamed>")
            context = c.get("context", "")
            risk = c.get("compromise_risk", "low")
            print(f"    {name}: {context} (risk: {risk})")


def view_secrecy(memory_dir: Path) -> None:
    state = load(memory_dir, "secrecy.json")
    if not state:
        print("(secrecy.json missing — run state_init.py)")
        return

    print(f"=== Secrecy / read-in (Day {state.get('as_of_day', '?')}) ===")
    inner = state.get("inner_circle", [])
    if inner:
        print(f"  Inner circle (full read-in): {len(inner)}")
        for member in inner:
            if isinstance(member, str):
                print(f"    - {member}")
            else:
                print(f"    - {member.get('name')}: {member.get('notes', '')}")
    partial = state.get("partial_read_in", [])
    if partial:
        print(f"  Partial read-in: {len(partial)}")
        for member in partial:
            print(f"    - {member.get('name')}: {member.get('topics', [])}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--what",
                    choices=["research", "fleet", "locations", "threads", "cover", "secrecy", "all"],
                    default="all")
    ap.add_argument("--memory-dir", type=Path, default=None)
    args = ap.parse_args()

    memory_dir = args.memory_dir or find_memory_dir()

    if args.what in ("research", "all"):
        view_research(memory_dir)
        print()
    if args.what in ("fleet", "all"):
        view_fleet(memory_dir)
        print()
    if args.what in ("locations", "all"):
        view_locations(memory_dir)
        print()
    if args.what in ("threads", "all"):
        view_threads(memory_dir)
        print()
    if args.what in ("cover", "all"):
        view_cover(memory_dir)
        print()
    if args.what in ("secrecy", "all"):
        view_secrecy(memory_dir)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
