---
name: rpg-audit
description: Use every 15–20 RPG turns, or when canon may have drifted, to find entities, agreements, and world facts that live only in the transcript.
disable-model-invocation: true
allowed-tools: Bash(python *skills/rpg/tools/*) Read Grep
---

# /rpg-audit

```!
python "${CLAUDE_SKILL_DIR}/../rpg/tools/registry_build.py" --check 2>&1
python "${CLAUDE_SKILL_DIR}/../rpg/tools/ledger.py" show 2>&1 | head -2
```

Then answer, from the transcript since the last audit:

1. Named entities introduced without files?
2. Contracts, agreements, or consequences living in transcript only?
3. Time-evolving world facts tracked in your head rather than a file?
4. DANGLING or UNINDEXED above? (DANGLING is blocking.)
5. `MEMORY.md`'s stated day equals the ledger day above?
6. `feedback_difficulty_variety.md` present and loaded?

List each gap with the file you would write. Propose: *"File these now, or at the next quiet beat?"* Detect only; the player decides.
