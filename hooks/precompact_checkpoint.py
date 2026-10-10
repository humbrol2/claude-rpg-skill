#!/usr/bin/env python3
"""PreCompact hook: write a continuity checkpoint before context is compacted.

Compaction is where transcript-only canon dies. This hook runs before every
compaction (auto or manual) in a session that booted /rpg, and writes
<memory>/sessions/checkpoint.md containing:
  - the last few assistant narration turns verbatim (the scene in progress)
  - the ledger line, so money survives the summary
  - the last beats and open HOT threads
Boot reads the checkpoint when sessions/last_session.md is missing or stale,
so a session that never reached /end still hands off cleanly.

Registered from SKILL.md's `hooks:` frontmatter, so it only exists once the
skill has been invoked this session.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import find_campaign_dir, load_ledger  # noqa: E402
from stop_review import find_memory_dir, session_booted_rpg  # noqa: E402

# Enough to reconstruct the scene in progress; more than this and the
# checkpoint becomes a second transcript.
KEEP_TURNS = 4
MAX_CHARS_PER_TURN = 3000


def last_assistant_texts(transcript: Path, n: int) -> list[str]:
    texts: list[str] = []
    if not transcript.exists():
        return texts
    with open(transcript, "r", encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("type") != "assistant":
                continue
            content = entry.get("message", {}).get("content", [])
            if isinstance(content, str):
                content = [{"type": "text", "text": content}]
            chunk = "\n".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text").strip()
            if chunk:
                texts.append(chunk)
    return texts[-n:]


def write_checkpoint(memory_dir: Path, transcript: Path, trigger: str) -> Path:
    ledger = load_ledger(memory_dir)
    liq = ledger.get("liquid", {})
    liq_s = ", ".join(f"{v} {k}" for k, v in liq.items()) if isinstance(liq, dict) else str(liq)
    lines = [
        f"# Checkpoint — written before {trigger} compaction, {datetime.now():%Y-%m-%d %H:%M}",
        "",
        f"Ledger: Day {ledger.get('as_of_day', '?')}, liquid {liq_s or 'n/a'}.",
        "",
    ]
    try:
        from track import status_text  # noqa: E402
        lines += ["## Tracking", status_text(memory_dir), ""]
    except Exception as exc:
        lines += [f"Tracking unavailable ({exc})", ""]
    lines.append("## Last narration turns (verbatim, newest last)")
    for i, text in enumerate(last_assistant_texts(transcript, KEEP_TURNS), 1):
        if len(text) > MAX_CHARS_PER_TURN:
            text = text[:MAX_CHARS_PER_TURN] + " …[truncated]"
        lines += [f"### Turn -{KEEP_TURNS - i + 1}", text, ""]
    lines += ["## Unfiled canon",
              "Anything named in the turns above that has no entity file is transcript-only. "
              "File it before continuing narration."]
    out = memory_dir / "sessions" / "checkpoint.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def main() -> int:
    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        hook_input = {}
    cwd = Path(hook_input.get("cwd", str(Path.cwd())))
    transcript = Path(hook_input.get("transcript_path", ""))
    memory_dir = find_memory_dir(cwd)
    if memory_dir is None or not transcript.exists() or not session_booted_rpg(transcript):
        print(json.dumps({}))
        return 0
    try:
        out = write_checkpoint(memory_dir, transcript, hook_input.get("trigger", "auto"))
    except Exception as exc:  # never block compaction over a checkpoint failure
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreCompact",
                                                 "additionalContext": f"RPG checkpoint failed: {exc}"}}))
        return 0
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreCompact",
        "additionalContext": f"RPG checkpoint written to {out}. After compaction, re-read it and "
                             f"the ledger before narrating; file any unfiled canon it lists."}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
