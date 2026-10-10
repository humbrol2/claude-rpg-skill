#!/usr/bin/env python3
"""One-screen campaign state for session boot.

Usage: python boot_summary.py [--memory-dir PATH] [--full-index]

Printed by SKILL.md's dynamic-context line when /rpg is invoked, and by the
SessionStart hook. Covers: canon integrity (DANGLING / UNINDEXED), ledger,
threads, pressures, last beats with the variety flag, checkpoint / last
session pointers, and the standing-rule file count. Never raises: a broken
tracking file becomes one line of output, because the campaign must always
be bootable without the tooling.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import find_memory_dir, load_ledger  # noqa: E402


def orphan_lines(memory_dir: Path) -> list[str]:
    try:
        from registry_build import orphan_report  # noqa: E402
        rep = orphan_report(memory_dir)
    except Exception as exc:  # the index check is advisory; never block boot on it
        return [f"Orphan check unavailable ({exc}) — skim MEMORY.md links manually."]
    if not rep["has_index"]:
        return ["No MEMORY.md — new or empty campaign directory."]
    lines = [f"Canon index: {rep['referenced']} files referenced, {rep['on_disk']} on disk."]
    if rep["dangling"]:
        lines.append(
            f"**DANGLING ({len(rep['dangling'])}) — BLOCKING, resolve with the player before narrating:** "
            + ", ".join(rep["dangling"][:10]) + (" …" if len(rep["dangling"]) > 10 else ""))
    if rep["unindexed"]:
        lines.append(f"UNINDEXED ({len(rep['unindexed'])}): "
                     + ", ".join(rep["unindexed"][:10]) + (" …" if len(rep["unindexed"]) > 10 else ""))
    if not rep["dangling"] and not rep["unindexed"]:
        lines.append("Index and disk agree — CLEAN.")
    return lines


def build_summary(memory_dir: Path, include_index: bool = False) -> str:
    lines = [f"Memory directory: {memory_dir}", ""]

    mem_index = memory_dir / "MEMORY.md"
    if include_index and mem_index.exists():
        lines += ["### Memory index (MEMORY.md)", "```", mem_index.read_text(encoding="utf-8").strip(), "```", ""]

    lines.append("### Canon integrity")
    lines += orphan_lines(memory_dir)
    lines.append("")

    try:
        ledger = load_ledger(memory_dir)
    except Exception as exc:
        ledger, lines = {}, lines + [f"### Ledger: unreadable ({exc}) — fix economy/ledger.json before any money narration", ""]
    if ledger:
        liq = ledger.get("liquid", {})
        liq_s = ", ".join(f"{v} {k}" for k, v in liq.items()) if isinstance(liq, dict) else str(liq)
        lines.append(f"### Ledger (Day {ledger.get('as_of_day', '?')})")
        lines.append(f"  Liquid: {liq_s or 'not set'}")
        n_in, n_out = len(ledger.get("monthly_inflows") or []), len(ledger.get("monthly_outflows") or [])
        if n_in or n_out:
            lines.append(f"  Recurring: {n_in} inflow(s), {n_out} outflow(s)")
        lines.append("")
    else:
        lines += ["### Ledger: none — ask before any economy narration", ""]

    try:
        from track import status_text  # noqa: E402
        lines += ["### Threads, pressures, beats", status_text(memory_dir), ""]
    except Exception as exc:
        lines += [f"Tracking files unavailable ({exc}).", ""]

    feedback = sorted(p.name for p in memory_dir.glob("feedback_*.md"))
    lines.append(f"### Standing rules: {len(feedback)} feedback file(s)" + (" — read all of them before narrating." if feedback else ""))
    lines.append("")

    for rel, note in (("sessions/last_session.md", "read it during bootstrap"),
                      ("sessions/checkpoint.md", "auto-checkpoint from the last compaction; read it if last_session.md is missing or older")):
        if (memory_dir / rel).exists():
            lines.append(f"{rel} present — {note}.")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("memory_dir_pos", nargs="?", type=Path, default=None,
                    help="campaign directory (positional form, as typed after /rpg)")
    ap.add_argument("--memory-dir", type=Path, default=None)
    ap.add_argument("--full-index", action="store_true", help="also print MEMORY.md verbatim")
    args = ap.parse_args()
    try:
        memory_dir = args.memory_dir or args.memory_dir_pos or find_memory_dir()
    except Exception as exc:
        print(f"No campaign memory directory found ({exc}). Ask the player which campaign, or start a new one.")
        return 0
    print(build_summary(memory_dir, include_index=args.full_index))
    return 0


if __name__ == "__main__":
    sys.exit(main())
