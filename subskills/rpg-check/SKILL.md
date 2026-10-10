---
name: rpg-check
description: Use mid-campaign when the player wants to give feedback on what is working, what feels flat, and what they want more of.
disable-model-invocation: true
---

# /rpg-check

Ask the player three questions in one message:

1. What's working?
2. What's feeling flat or repetitive?
3. Anything you want more of?

Write the answers verbatim to `<memory>/feedback_live.md` (frontmatter: name, description, type: feedback) and add its `MEMORY.md` line. Then adjust narration for the rest of the session accordingly. Do not argue with or qualify the answers — record and apply.
