---
name: rpg-end
description: Use when the player is finishing an RPG session, to close it out cleanly so the next session boots from disk, not from memory.
disable-model-invocation: true
allowed-tools: Bash(python *skills/rpg/tools/*) Read Write Edit
---

# /rpg-end

Follow `${CLAUDE_SKILL_DIR}/../rpg/reference/session-end.md` exactly, in order. Read it now.

```!
python "${CLAUDE_SKILL_DIR}/../rpg/tools/registry_build.py" --check 2>&1
python "${CLAUDE_SKILL_DIR}/../rpg/tools/track.py" status 2>&1
```

Finish with one line: *Session closed at Day N. last_session.md written. Index CLEAN / N gaps resolved.*
