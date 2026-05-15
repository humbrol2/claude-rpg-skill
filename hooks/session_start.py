#!/usr/bin/env python3
"""SessionStart hook for RPG mode.

Detects whether the current chat is operating in an RPG context (by checking
for a campaign memory directory) and, if so, builds the registry and emits a
canon summary as additionalContext for the session.

Designed to be invoked from ~/.claude/settings.json as a SessionStart hook.
Emits a JSON envelope on stdout per Claude Code hook contract.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass


def find_memory_dir() -> Path | None:
    """Find an RPG memory directory near the CWD or in known project locations."""
    cwd = Path.cwd()

    # Walk up from CWD looking for RPG_CAMPAIGN.md or memory/MEMORY.md
    for ancestor in [cwd] + list(cwd.parents):
        if (ancestor / "RPG_CAMPAIGN.md").exists():
            for line in (ancestor / "RPG_CAMPAIGN.md").read_text(encoding="utf-8").splitlines():
                if ":" in line and "memory_dir" in line:
                    path_str = line.split(":", 1)[1].strip()
                    candidate = Path(path_str).expanduser()
                    if candidate.exists():
                        return candidate
        if (ancestor / "memory" / "MEMORY.md").exists():
            return ancestor / "memory"
        if ancestor == ancestor.parent:
            break

    # Check ~/.claude/projects/*/memory
    home = Path.home() / ".claude" / "projects"
    if home.exists():
        # Match by current working directory mapping
        cwd_marker = str(cwd).replace(":", "-").replace("\\", "-").replace("/", "-")
        for project_dir in home.iterdir():
            if not project_dir.is_dir():
                continue
            if cwd_marker.lower() in project_dir.name.lower():
                mem = project_dir / "memory"
                if (mem / "MEMORY.md").exists():
                    return mem
    return None


def build_summary(memory_dir: Path) -> str:
    """Compose a tight RPG-state summary for session bootstrap."""
    lines = []
    lines.append("**RPG context detected.** Operating in RPG mode for this session.")
    lines.append(f"Memory directory: {memory_dir}")
    lines.append("")

    # Skill reference
    lines.append("Skill instructions: ~/.claude/skills/rpg/SKILL.md")
    lines.append("")

    # MEMORY.md index (lightweight)
    mem_index = memory_dir / "MEMORY.md"
    if mem_index.exists():
        text = mem_index.read_text(encoding="utf-8")
        lines.append("### Memory index (MEMORY.md)")
        lines.append("```")
        lines.append(text.strip())
        lines.append("```")
        lines.append("")

    # Registry stats
    registry = memory_dir / "registry.json"
    if registry.exists():
        with open(registry, "r", encoding="utf-8") as f:
            reg = json.load(f)
        lines.append(f"### Canon registry: {reg.get('count', 0)} entities")
        for type_name, names in reg.get("by_type", {}).items():
            lines.append(f"  - {type_name}: {len(names)}")
        lines.append("")

    # Ledger
    ledger_path = memory_dir / "economy" / "ledger.json"
    if ledger_path.exists():
        with open(ledger_path, "r", encoding="utf-8") as f:
            ledger = json.load(f)
        liq = ledger.get("liquid", {})
        total_liq = sum(v for k, v in liq.items() if k != "floor")
        weekly_realized = sum(i.get("amount", 0) for i in ledger.get("weekly_realized_inflows", []))
        weekly_unrealized = sum(v.get("valuation", 0) * v.get("weekly_unrealized_gain_pct", 0) / 100
                                 for v in ledger.get("vehicles", []))
        lines.append(f"### Ledger (Day {ledger.get('as_of_day', '?')})")
        lines.append(f"  Liquid: ${total_liq:.2f}M")
        lines.append(f"  Weekly profit: ~${weekly_realized + weekly_unrealized:.2f}M combined")
        lines.append("")

    # State files
    state_dir = memory_dir / "state"
    if state_dir.exists():
        for name in ("character.json", "research.json", "fleet.json", "locations.json",
                     "threads.json", "cover.json", "secrecy.json"):
            path = state_dir / name
            if not path.exists():
                continue
            with open(path, "r", encoding="utf-8") as f:
                s = json.load(f)
            # Summarize one-line per file
            if name == "character.json":
                true_name = s.get("true_name", "<unset>")
                covers = len(s.get("cover_identities", []))
                heritage = len(s.get("heritage_standings", []))
                lines.append(f"  PC: {true_name} ({covers} cover identities, {heritage} heritage standings)")
            elif name == "research.json":
                domains = len(s.get("domains", []))
                projects = len([p for p in s.get("active_projects", []) if p.get("progress_pct", 0) < 100])
                lines.append(f"  Research: {domains} domains, {projects} active projects")
            elif name == "fleet.json":
                ships = len(s.get("ships", []))
                droid_total = s.get("droids", {}).get("total", 0)
                lines.append(f"  Fleet: {ships} ships, {droid_total} droids")
            elif name == "locations.json":
                bases = len(s.get("bases", []))
                stations = len(s.get("stations", []))
                construction = len([c for c in s.get("construction_sites", [])
                                    if c.get("completion_pct", 0) < 100])
                lines.append(f"  Locations: {bases} bases, {stations} stations, {construction} active construction")
            elif name == "threads.json":
                open_t = len(s.get("open_threads", []))
                lines.append(f"  Open threads: {open_t}")
            elif name == "cover.json":
                covers = len(s.get("active_covers", []))
                lines.append(f"  Cover identities: primary={s.get('primary_identity', '<unset>')}, {covers} active covers")
            elif name == "secrecy.json":
                inner = len(s.get("inner_circle", []))
                partial = len(s.get("partial_read_in", []))
                lines.append(f"  Read-in: {inner} inner-circle, {partial} partial")
        lines.append("")

    # Reminders
    lines.append("### Mandatory disciplines (from SKILL.md)")
    lines.append("- **Canon-check before invoking any named entity.** Run `python ~/.claude/skills/rpg/tools/canon_check.py <name>` if uncertain. NOT FOUND → ask user, do not invent.")
    lines.append("- **Ledger consult before any numerical financial claim.** Run `python ~/.claude/skills/rpg/tools/ledger_state.py`. Always report numbers from the ledger, never from working memory.")
    lines.append("- **Time-skip default 1 week max** unless user explicitly approves longer. Each skip runs ledger_advance + state_advance.")
    lines.append("- **Major scenes pause for PC dialogue.** Set the scene, NPCs speak, hand the floor to the player.")
    lines.append("- **Concise updates.** Bullets, lead with changes, skip steady-state, always end with liquid + weekly profit line.")
    lines.append("")
    lines.append("If anything is uncertain — **defer to the user, do not invent.**")

    return "\n".join(lines)


def main() -> int:
    memory_dir = find_memory_dir()
    if memory_dir is None:
        # Not in an RPG context — emit nothing
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": ""}}))
        return 0

    summary = build_summary(memory_dir)
    envelope = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": summary,
        }
    }
    print(json.dumps(envelope))
    return 0


if __name__ == "__main__":
    sys.exit(main())
