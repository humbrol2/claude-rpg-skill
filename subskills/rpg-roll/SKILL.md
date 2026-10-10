---
name: rpg-roll
description: Use during an RPG session to roll dice for an uncertain outcome instead of deciding the result in narration.
argument-hint: "<dice> [--adv|--dis]  e.g. d20+5 2d6"
disable-model-invocation: true
allowed-tools: Bash(python *skills/rpg/tools/*)
---

# /rpg-roll

```!
python "${CLAUDE_SKILL_DIR}/../rpg/tools/roll.py" $ARGUMENTS 2>&1
```

State the target number or difficulty *before* interpreting the result, then report the roll exactly as printed and narrate the outcome it gives. Never re-roll or adjust.
