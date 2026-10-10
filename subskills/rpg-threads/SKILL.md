---
name: rpg-threads
description: Use during an RPG session to list all tracked story threads by status (HOT, WARM, COOL, STALE) and decide which to advance.
argument-hint: "[--all]"
disable-model-invocation: true
allowed-tools: Bash(python *skills/rpg/tools/*)
---

# /rpg-threads

```!
python "${CLAUDE_SKILL_DIR}/../rpg/tools/track.py" threads $ARGUMENTS 2>&1
```

Show the list grouped by status. For STALE threads (100+ days unadvanced) propose, in one line each, which 2–3 to advance next and the natural beat for each. Close any the player says are done: `track.py thread-set --id X --status CLOSED`.
