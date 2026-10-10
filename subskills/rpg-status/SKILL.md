---
name: rpg-status
description: Use during an RPG session for a tight current-state snapshot — day, liquid, hot threads, high pressures, last beats.
disable-model-invocation: true
allowed-tools: Bash(python *skills/rpg/tools/*)
---

# /rpg-status

```!
python "${CLAUDE_SKILL_DIR}/../rpg/tools/track.py" status 2>&1
python "${CLAUDE_SKILL_DIR}/../rpg/tools/ledger.py" show 2>&1 | head -4
```

Report the above as 5–10 bullets: what changed since the last status, pending decisions, then liquid and income rate on the last line. Do not add anything not in the output or the campaign files.
