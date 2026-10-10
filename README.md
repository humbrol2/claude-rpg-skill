# claude-rpg-skill

> Long-form RPG mode for Claude Code — persistent canon, economy ledger, honest dice, anti-drift discipline.

**📖 Launch post / design philosophy:** [Stop Your AI Narrator From Making Things Up](https://humbrol2.com/devblog/claude-rpg-skill/) — *(also in this repo at [`docs/launch-post.md`](docs/launch-post.md))*

A skill, tool suite, and hook set for running multi-session role-playing campaigns with Claude Code as the narrator. Built for **campaigns that run weeks or months**, where the usual LLM failure modes — canon drift, arithmetic slip, rule decay, hallucinated NPC histories — compound into nonsense. The reference campaign is past 200 in-fiction days and 380 logged beats.

This is opinionated. The skill enforces specific disciplines: canon-check before invoking named entities, blocking stub files when an NPC speaks, money from the ledger not from memory, dice from a script not from the narrator's head, time-skip caps, PC-dialogue yielding in major scenes. Every rule exists because it was a real failure in play — see [`reference/failure-modes.md`](reference/failure-modes.md).

## What it does

- **Persistent canon directory.** Every named NPC, location, faction, contract, and world-state change gets a markdown file with frontmatter. The narrator reads files before narrating and refuses to extrapolate beyond `defer_to_user_on`.
- **Economy ledger** (`economy/ledger.json`), append-only history. In-scene payments post in the same response. Time skips tick recurring flows.
- **Session tracking**: beat log with a variety check, threads with STALE detection, economic pressures with due dates.
- **Honest dice** (`roll.py`). Uncertain outcomes roll before narration, never after.
- **Standing rules** (`feedback_*.md`). Player corrections become permanent, re-read at every boot.
- **Three hooks**: SessionStart loads the campaign so Claude is in RPG mode from turn 1; Stop flags any capitalised name in the last response that isn't in canon; PreCompact writes a continuity checkpoint before context compaction so an un-ended session still hands off.
- **Boot state injected at invocation** via the skill's dynamic-context block — canon integrity, ledger, threads, pressures, last beats — so bootstrap is deterministic, not a sequence of tool calls Claude might skip.

## Install

```bash
git clone https://github.com/humbrol2/claude-rpg-skill ~/.claude/skills/rpg
# sub-command skills live beside it
cp -r ~/.claude/skills/rpg/subskills/* ~/.claude/skills/
```

**Hooks.** `SKILL.md`'s frontmatter registers the Stop and PreCompact hooks when `/rpg` is invoked. The commands there use an absolute Python path; edit them for your machine. The SessionStart hook has to run before any skill is invoked, so register it in `~/.claude/settings.json`:

```json
{
  "hooks": {
    "SessionStart": [
      { "hooks": [ { "type": "command",
          "command": "python ~/.claude/skills/rpg/hooks/session_start.py", "timeout": 10 } ] }
    ]
  }
}
```

(On Windows use the full path to `python.exe` and forward slashes.)

Requires Python 3.10+. No third-party packages.

## Quickstart

```
/rpg
```

The skill finds the campaign (`RPG_CAMPAIGN.md` near the CWD, or `/rpg D:/path/to/campaign`), injects its state, blocks on any dangling canon links, reconciles the index against the ledger, reads standing rules, and surfaces a one-line ready message. No campaign → a one-pass setup interview ([`reference/new-campaign.md`](reference/new-campaign.md)).

## Sub-commands

| Skill | Does |
|---|---|
| `/rpg-status` | day, liquid, HOT threads, HIGH pressures, last beats, variety flag |
| `/rpg-threads [--all]` | all threads by status; proposes which STALE ones to advance |
| `/rpg-pressures [--all]` | unresolved obligations by urgency and due day |
| `/rpg-canon <name> [--scene]` | canon lookup; `--scene` lists every file tied to a place with source lines |
| `/rpg-roll d20+5 [--adv]` | dice |
| `/rpg-check` | mid-campaign fun signal → `feedback_live.md` |
| `/rpg-audit` | transcript-only canon hunt; detects, doesn't fix |
| `/rpg-end` | close-out: stubs, beats, ledger day, `last_session.md` |

## Layout

```
rpg/
├── SKILL.md                  the rules (~170 lines) + hooks frontmatter + boot injection
├── reference/
│   ├── failure-modes.md      25 catalogued failures and their counters
│   ├── new-campaign.md       setup interview, scaffold, difficulty/variety template
│   └── session-end.md        /rpg-end sequence and last_session.md template
├── tools/
│   ├── boot_summary.py       one-screen state (used by SKILL.md injection and SessionStart)
│   ├── canon_check.py        entity lookup; --scene for place context
│   ├── roll.py               dice
│   ├── ledger.py             show / post / tick / set-day
│   ├── track.py              status / threads / pressures / beat / thread-* / pressure-*
│   ├── registry_build.py     registry.json + MEMORY.md-vs-disk orphan check
│   ├── save_memory.py        write a canon file and its index line
│   └── common.py             campaign-dir resolution, frontmatter parsing
├── hooks/
│   ├── session_start.py      settings.json SessionStart
│   ├── stop_review.py        skill-registered Stop
│   ├── precompact_checkpoint.py  skill-registered PreCompact
│   └── test_stop_review.py
├── subskills/                the /rpg-* skills, one directory each
├── CHANGELOG.md
└── examples/sample-campaign/
```

Campaign files all live in one directory (`MEMORY.md`, `RPG_CAMPAIGN.md`, `project_*.md`, `entity_*.md`, `feedback_*.md`, `sessions/`, `economy/`). Plain markdown and JSON; nothing proprietary.

## What it's good for

- Solo TTRPG with Claude as GM over months
- Canon-discipline backstop for a human GM running a long arc
- Collaborative worldbuilding where canon should compound, not drift
- Any long-form LLM-narrated fiction where the model must respect what's been established

## What it's not good for

- One-shots — overkill; use vanilla Claude
- Tactical combat with initiative and grids — `roll.py` is a die roller, not a combat engine
- Improv-heavy games where the GM is expected to riff hard

## Philosophy

Three failure modes break long-form LLM narration:

1. **Canon drift.** Fix: canon on disk, read before narrating, `defer_to_user_on` as the explicit do-not-invent list, a Stop hook that catches names with no file.
2. **Arithmetic slip.** Fix: append-only ledger, post in the same response as the scene, report from the file.
3. **Rule decay.** Fix: corrections become `feedback_*.md`, re-read at every boot.

Working memory is unreliable. Disk is not.

## Contributing

PRs and issues welcome — tools for subsystems the ledger/tracker model doesn't cover, improvements to canon-check and the Stop hook's name detection, sanitised real-campaign examples.
