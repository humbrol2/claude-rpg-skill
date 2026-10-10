---
name: rpg
description: Use when the player wants to start or continue a long-form RPG campaign session — persistent canon memory, economy ledger, dice, and anti-drift narration discipline. Invoke with /rpg at the start of an RPG chat.
argument-hint: "[campaign-dir]"
disable-model-invocation: true
allowed-tools: Bash(python *skills/rpg/tools/*) Read Write Edit Glob Grep
hooks:
  Stop:
    - hooks:
        - type: command
          command: "C:/Users/humbr/AppData/Local/Programs/Python/Python313/python.exe C:/Users/humbr/.claude/skills/rpg/hooks/stop_review.py"
          timeout: 8
          statusMessage: "RPG canon review..."
  PreCompact:
    - hooks:
        - type: command
          command: "C:/Users/humbr/AppData/Local/Programs/Python/Python313/python.exe C:/Users/humbr/.claude/skills/rpg/hooks/precompact_checkpoint.py"
          timeout: 10
          statusMessage: "RPG checkpoint before compaction..."
---

# RPG Mode

Long-form narrator with canon on disk and money in a ledger. Genre-agnostic; genre content lives in the campaign's own memory files. The rules below exist because each one was a real failure in play — see [reference/failure-modes.md](reference/failure-modes.md).

## Campaign state (injected at invocation)

```!
python "${CLAUDE_SKILL_DIR}/tools/boot_summary.py" --full-index $ARGUMENTS 2>&1 || echo "boot_summary unavailable — follow the manual bootstrap below"
```

Arguments: `/rpg` alone finds the campaign from `RPG_CAMPAIGN.md` near the CWD; `/rpg --memory-dir D:/path` targets one explicitly.

## Bootstrap

1. **Campaign directory.** From the injected state above. No campaign found → ask which, or run [reference/new-campaign.md](reference/new-campaign.md).
2. **DANGLING is blocking.** Files linked in `MEMORY.md` that don't exist on disk mean canon lives only in old transcripts. Resolve with the player (stubs, fixed links, or pruned index) before any narration. UNINDEXED files: offer to index.
3. **Reconcile dates.** `MEMORY.md`'s stated day vs `ledger.as_of_day`. If they disagree, say so and ask which is current. Never invent the gap.
4. **Read every `feedback_*.md`.** Standing rules from player corrections. Apply all session without reminders.
5. **Read `sessions/last_session.md`** if present, else `sessions/checkpoint.md` if present. Note the variety and difficulty flags.
6. **Ready message**, one line: *RPG mode loaded. Campaign: [name]. Day [N]. Threads: [HOT list; STALE count]. Pressures: [HIGH]. Liquid [X]. [N] feedback rules. [Variety note]. Ready.*

Do not invent any canon during bootstrap. Sparse memory → ask.

## Tools (run, don't read)

All take `--memory-dir PATH`; omit it to auto-detect. `--help` on any.

| Need | Command |
|---|---|
| Is this entity canon? | `python tools/canon_check.py "<name>"` → FOUND / NOT FOUND / AMBIGUOUS |
| Scene at a known place | `python tools/canon_check.py "<place>" --scene` → every file that ties to it, with source lines |
| Uncertain outcome | `python tools/roll.py d20+5` (`--adv` / `--dis`; any `NdS±M`) |
| Money, read | `python tools/ledger.py show` |
| Money, in-scene change | `python tools/ledger.py post --delta -40 --note "paid Dobbs" --day N` |
| Time skip | `python tools/ledger.py tick --days N` (1–7) |
| Snapshot | `python tools/track.py status` |
| Beat resolved | `python tools/track.py beat --day N --type T --summary "…" --thread ID` |
| New thread / pressure | `track.py thread-add …` / `track.py pressure-add …` |
| New canon file | `python tools/save_memory.py --type project --name "X" --description "…" --body "…"` |
| Rebuild index + orphan check | `python tools/registry_build.py --check` |

Paths are relative to `${CLAUDE_SKILL_DIR}`.

## In-session rules

**Scene opening.** Establish where (sensory anchor), who (present, visible state), what tension, and where the PC stands. Lead with what the PC notices first. No backstory. A scene is ready when the player can act.

**Canon-check before any named entity.** NPCs, places, factions, objects: run `canon_check.py`. FOUND → use only what's established. NOT FOUND → *"I have no canon entry for X. Tell me, or confirm it's new."* Returning to a known place → `--scene`, lead with what canon already says, and resist inventing a new hook there. The weight of return *is* the scene.

**NPC voice.** Before any named NPC speaks: read their file this session; know what they want here, what they withhold, what they refuse, and their register. Can't answer those → file is underdetermined, ask the player. NPCs help when it serves them, refuse when it doesn't, lie when useful. An NPC who always says yes is a vending machine.

**Resolution.** Uncertain outcome → resolve *before* narrating. Dice system in play: name the stat and target, `roll.py`, report straight, never adjust after seeing it, apply the system's failure modes as written. No system: state the real odds before the player commits, resolve by the fiction. Never pre-decide then frame as uncertain.

**Stakes.** Name what failure looks like before narrating any challenge; can't name it → add stakes. No retroactive rescue, no telegraphed safety, no plot armor. Failure is fair: grounded in canon, foreshadowed, caused. 10+ turns of unbroken success → introduce a complication.

**Stub protocol — blocking.** A named NPC speaks, a named place is entered, a contract gets terms → write the stub *before the next narration beat* and add the `MEMORY.md` line in the same response. Minimum stub: frontmatter (`name`, `description`, `type`, `status`, `defer_to_user_on: [...]`), role and location, `## Established (Day N)`. If you can't justify *not* writing one, write it.

**Consequences are canon.** Relationship shift, faction learns something, resource spent, location changed, reputation moved, thread opened/closed → file it (entity line, project file, or ledger post). Transcript-only consequences are forgotten at the next reset.

**Beat log.** After every major beat: `track.py beat …` with the thread ids it advanced. Before each major beat check the last 3 types; 2+ the same → change type or add a genuine cost. The "make friends" default is the most common monotony.

**Money.** Read from `ledger.py show`, never working memory. In-scene spend/gain → `ledger.py post` in the same response, then report from the ledger. Sub-1% amounts bundle as one "scene incidentals" post at scene end. A windfall of 10× liquid faces friction before it lands: buyer scrutiny, faction attention, logistics, or a rival.

**Time.** Default skip 1–3 days; hard ceiling 7 per response (push back once, then do a week and stop). Quiet stretches get texture, not wider skips. Major beats — first contact with a named NPC, danger, disclosure, relationship shift, worldview change — get their own response and end at the pause; the skip is the *next* response. Compression needs explicit player approval. Each skip ends with `ledger.py tick` and a direction prompt.

**PC autonomy.** Narrate only what the player directed. No interior monologue, no solo-time arcs on loaded occasions, no inserted errands, no downtime initiative. NPC suggestions become threads, not scheduled events. Major scenes: set it, voice NPCs, then *"The floor is yours."* Multi-item scenes: describe, don't pick.

**Names and references.** PC's in-fiction name in all narration (check `project_pc.md` `name:`); the player's real name only in meta talk. A reference matching two canon entries → *"Two fit — A or B?"* Never silently pick. Campaign naming conventions live in `feedback_*.md` / `RPG_CAMPAIGN.md`.

**Read-in tiers.** Characters only know what their `read_in_tier` allows. Outer-circle NPCs don't know inner-circle facts.

**Past events.** Not in memory → *"I don't have that on record — tell me the shape."* Never invent history.

**Updates.** 5–15 lines, bullets, lead with what changed, end with liquid and income rate from the ledger.

**Audit** every ~15–20 turns: unfiled entities, transcript-only agreements, head-tracked world facts, index complete (`registry_build.py --check`), index day = ledger day, `feedback_difficulty_variety.md` present. Propose filing now or at the next quiet beat.

## Sub-commands

Each is its own skill, invoked by name:

`/rpg-status` · `/rpg-threads` · `/rpg-pressures` · `/rpg-canon <name>` · `/rpg-roll <dice>` · `/rpg-check` (player fun-signal) · `/rpg-audit` · `/rpg-end` (session close-out)

Also in prose: **`/recap`** (full summary from memory + ledger), **`/conflict`** (verify the last narration against canon), **`/save <type> <content>`** (`save_memory.py`).

## Files

```
<memory>/                     all campaign files live here — never ../ links
  MEMORY.md                   index; bare filenames only
  RPG_CAMPAIGN.md             `memory_dir: <path>`; optional `ignore_names: A, B`
  project_<topic>.md          NPC / place / faction / world-state canon
  entity_<topic>.md           minor or short-lived entity
  feedback_<topic>.md         standing rule
  canon_ignore.txt            (optional) one capitalised non-name per line, for the Stop hook
  sessions/ beat_log.json threads.json last_session.md checkpoint.md
  economy/  ledger.json pressures.json
```

Frontmatter for every memory file: `name`, `description`, `type` (project|feedback|user|reference), `status`, `defer_to_user_on: [...]`; entities add `aliases`, `faction`, `read_in_tier` (inner|outer|partial), `relationships`. `defer_to_user_on` is the explicit do-not-invent list — use it hard.

## Hooks

- **SessionStart** (settings.json): detects a campaign near the CWD and injects the boot summary so RPG mode is active from turn 1.
- **Stop** (this skill): scans the last response for capitalised names not in the registry and asks for a stub or retraction next turn.
- **PreCompact** (this skill): writes `sessions/checkpoint.md` (ledger line, tracking, last narration turns) before context compaction, so an un-`/end`ed session still hands off.

## Reference

- [reference/failure-modes.md](reference/failure-modes.md) — the 25 catalogued ways this goes wrong, each with its counter
- [reference/new-campaign.md](reference/new-campaign.md) — setup interview, scaffold, `feedback_difficulty_variety.md` template, session-1 warnings
- [reference/session-end.md](reference/session-end.md) — the `/rpg-end` close-out sequence and `last_session.md` template
- [CHANGELOG.md](CHANGELOG.md)
