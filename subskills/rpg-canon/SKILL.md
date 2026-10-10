---
name: rpg-canon
description: Use during an RPG session to look up a named entity or place in campaign canon before narrating it.
argument-hint: "<name> [--scene]"
disable-model-invocation: true
allowed-tools: Bash(python *skills/rpg/tools/*) Read
---

# /rpg-canon

```!
python "${CLAUDE_SKILL_DIR}/../rpg/tools/canon_check.py" $ARGUMENTS 2>&1
```

FOUND → read the file named and summarise only what it establishes, including `defer_to_user_on`. NOT FOUND → tell the player there is no canon entry and ask whether it is new; do not invent. AMBIGUOUS → list the candidates and ask. With `--scene`, the output is every file tied to a place; lead the next scene with it.
