---
name: rpg-pressures
description: Use during an RPG session to list unresolved economic and time pressures (rent, debts, deadlines, supply gaps) by urgency.
argument-hint: "[--all]"
disable-model-invocation: true
allowed-tools: Bash(python *skills/rpg/tools/*)
---

# /rpg-pressures

```!
python "${CLAUDE_SKILL_DIR}/../rpg/tools/track.py" pressures $ARGUMENTS 2>&1
```

Show urgency and due days. Propose which to address at the next natural beat. Resolve with `track.py pressure-resolve --id X`; add new ones with `track.py pressure-add`.
