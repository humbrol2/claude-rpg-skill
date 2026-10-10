#!/usr/bin/env python3
"""SessionStart hook for RPG mode.

Detects whether the current chat is operating in an RPG context (a campaign
memory directory near the CWD, or this project's own memory dir) and, if so,
emits the boot summary from tools/boot_summary.py plus the mandatory
disciplines as additionalContext — so Claude operates in RPG mode from turn
1 even before /rpg is typed.

Registered in ~/.claude/settings.json as a SessionStart hook (it cannot live
in the skill's own hooks: frontmatter, because those only register once the
skill is invoked). Emits a JSON envelope on stdout per the hook contract.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))
from common import find_campaign_dir  # noqa: E402
from boot_summary import build_summary  # noqa: E402

DISCIPLINES = """### Mandatory disciplines (from SKILL.md)
- **Canon-check before invoking any named entity.** `python ~/.claude/skills/rpg/tools/canon_check.py <name>`; NOT FOUND → ask the player, do not invent.
- **Ledger consult before any financial claim.** Numbers come from `ledger.py show`, never working memory. In-scene payments: `ledger.py post` in the same response.
- **Time-skip default 1–3 days; hard ceiling 7 days per response.** Major beats get their own response; no chaining a beat to a skip.
- **NPC stubs are blocking.** A named NPC who speaks gets a stub file and a MEMORY.md index line before narration continues.
- **Major scenes pause for PC dialogue.** Set the scene, NPCs speak, hand the floor to the player. Never narrate the PC's interior or unstated actions.
- **Uncertain outcomes roll.** `roll.py` — never a result from the narrator's head.

If anything is uncertain — **defer to the player, do not invent.**"""


def find_memory_dir() -> tuple[Path, bool] | None:
    """(memory_dir, is_project_memory). The second is True when the directory
    is this project's own auto-memory dir, which the harness already loads
    into context, so the hook must not echo MEMORY.md a second time."""
    cwd = Path.cwd()
    campaign = find_campaign_dir(cwd)
    if campaign is not None:
        return campaign, False
    home = Path.home() / ".claude" / "projects"
    if home.exists():
        cwd_marker = str(cwd).replace(":", "-").replace("\\", "-").replace("/", "-")
        for project_dir in home.iterdir():
            if project_dir.is_dir() and cwd_marker.lower() in project_dir.name.lower():
                mem = project_dir / "memory"
                if (mem / "MEMORY.md").exists():
                    return mem, True
    return None


def main() -> int:
    found = find_memory_dir()
    if found is None:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": ""}}))
        return 0
    memory_dir, is_project_memory = found
    summary = "\n".join([
        "**RPG context detected.** Operating in RPG mode for this session. Invoke `/rpg` to boot fully.",
        "Skill instructions: ~/.claude/skills/rpg/SKILL.md",
        "",
        build_summary(memory_dir, include_index=not is_project_memory),
        DISCIPLINES,
    ])
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": summary}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
