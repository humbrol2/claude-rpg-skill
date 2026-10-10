# Session close-out (`/rpg-end`)

Run in this order. Each step writes to disk before the next; session end may be interrupted.

1. **Unfiled entities.** List named NPCs, places, and agreements from this session with no file. Write the stubs now and add their `MEMORY.md` lines. `python tools/registry_build.py --check` must come back CLEAN.
2. **Beats and threads.** Any major beat not yet in `beat_log.json` → `track.py beat …`. Threads resolved this session → `track.py thread-set --id X --status CLOSED`. New obligations → `track.py pressure-add …`.
3. **Ledger.** `ledger.py show`; confirm `as_of_day` is the closing in-fiction day (`ledger.py set-day N` if not). Every in-scene transaction this session has a history line.
4. **Write `sessions/last_session.md`:**

```markdown
# Session — Day X to Day Y
## Beat log
- [type] brief description
## New entities
- name — stub written Y/N
## Consequences filed
- description — filed Y/N
## Ledger delta
- Start: X / End: Y / Net: Z
## Open threads (carried forward)
- thread — status
## Difficulty & variety check
- Genuine cost faced: Y/N
- Beat types this session: [list]
- Monotony flag: Y/N
```

5. **`MEMORY.md` current-state header** → the closing scene, day, and time.
6. **Pending canon proposals** → confirm with the player or drop them.
7. Delete `sessions/checkpoint.md` if present; `last_session.md` supersedes it.
