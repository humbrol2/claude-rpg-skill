# claude-rpg-skill

> Long-form RPG mode for Claude Code — persistent canon, finance ledger, anti-drift discipline.

**📖 Launch post / design philosophy:** [Stop Your AI Narrator From Making Things Up](https://humbrol2.com/devblog/claude-rpg-skill/) — *(also in this repo at [`docs/launch-post.md`](docs/launch-post.md))*

A skill + tool suite for running long-form, multi-session role-playing campaigns with Claude Code as the narrator. Designed for **campaigns that run weeks or months** where the usual LLM failure modes — canon drift, arithmetic slip, rule decay, hallucinated NPC histories — compound into nonsense.

This is opinionated. The skill enforces specific disciplines (canon-check before invoking named entities, write stub files as entities stick, ledger-from-truth not from memory, time-skip caps, major-scene PC-dialogue yielding). Those disciplines are what make narration trustworthy at length.

## What it does

- **Persistent canon directory** (`<memory>/`). Every named NPC, location, ship, contract, hidden asset, and threat state gets a markdown file. The narrator consults files before invoking entities — no improvising on already-established lore.
- **Structured economy ledger** (`<memory>/economy/ledger.json`). All financial state lives here, append-only history. Liquid balances, vehicles, facilities, weekly inflows, policies. The narrator reads from the ledger, not from working memory.
- **Standing-rule overrides** (`feedback_*.md`). Player corrections become permanent operating rules. "Don't write PC dialogue in major scenes" or "transits are 1-2 days not 4-5" stick across sessions.
- **SessionStart hook** loads the campaign at boot — MEMORY.md, ledger snapshot, standing rules — so Claude operates in RPG mode from turn 1, not just on `/rpg` invocation.
- **Tool suite** (~14 Python scripts) for ledger ticks on time skips, canon checks, character init/view, registry builds, state advancement.

## Install

```bash
# 1. Clone into your Claude Code skills directory
git clone https://github.com/humbrol2/claude-rpg-skill ~/.claude/skills/rpg

# 2. Make hooks + tools executable (POSIX)
chmod +x ~/.claude/skills/rpg/hooks/*.py ~/.claude/skills/rpg/tools/*.py
```

The SessionStart hook (`hooks/session_start.py`) needs to be registered in your Claude Code `settings.json`. Example block:

```json
{
  "hooks": {
    "SessionStart": [
      { "command": "python ~/.claude/skills/rpg/hooks/session_start.py" }
    ]
  }
}
```

(Adjust the python path for Windows: `"C:/path/to/python.exe C:/Users/.../.claude/skills/rpg/hooks/session_start.py"`.)

## Quickstart

In any chat, invoke:

```
/rpg
```

The skill will:
1. Look for an existing campaign in the current working directory (`RPG_CAMPAIGN.md`) or in `~/.claude/projects/<project-id>/memory/`.
2. If found, load `MEMORY.md`, ledger, and standing rules.
3. If not found, ask you what campaign to start.

Then it surfaces a one-line ready state and waits for your first instruction.

From there, you direct the campaign. The narrator sets scenes, NPCs speak, you control the PC. The ledger updates on time skips. New entities get stub canon files as they stick.

## Sub-commands

Within an active session:

- **`/status`** — tight current-state snapshot (day, liquid, weekly profit, active projects, current location, pending decisions)
- **`/recap`** — fuller summary across all canon files
- **`/canon <name>`** — look up entity in memory
- **`/advance <N> days`** — tick the ledger + state forward N days
- **`/audit`** — periodic memory audit; identifies named entities, contracts, comm protocols, hidden assets, and threat states introduced in play but not yet filed
- **`/save <type> <content>`** — manually add a memory entry
- **`/conflict`** — verify everything just narrated against canon
- **`/end`** — close out the session cleanly

## What it's good for

- **Solo TTRPG** — Claude as your GM for a campaign you run alone over months
- **Co-narration assist** — Claude as a canon-discipline backstop for a human GM running a long arc
- **Worldbuilding sessions** — develop a setting collaboratively with canon that compounds rather than drifts
- **Any long-form LLM-narrated fiction project** where you need the model to remember and respect what's been established

## What it's *not* good for

- **One-shots** — overkill for a single session. Use vanilla Claude.
- **Combat-heavy tactical play** — there's no dice subsystem, no initiative tracker, no combat math beyond what you bring. The skill is narration-and-economy focused.
- **Settings where canon doesn't matter much** — improv-friendly games where the GM is expected to riff hard. The skill's discipline cuts against that.

## Philosophy

Three failure modes break long-form LLM narration. This skill addresses each:

1. **Canon drift.** The LLM half-remembers, fills in gaps, and twenty turns later the NPC who used to be a 60yo Tirran retiree is a 35yo human ex-corporate. Fix: write canon to disk, read it before narrating, refuse to extrapolate beyond it. The `defer_to_user_on` frontmatter field is the explicit "do not invent these axes" list.

2. **Arithmetic slip.** Money moves a credit here, a credit there, and by month three the running totals don't match anything that actually happened. Fix: append-only history in `ledger.json`, periodic reconciliation, narrator reads finance from the ledger not working memory.

3. **Rule decay.** Player corrects the narrator on something — "transits are too long" — and a week later the same mistake. Fix: corrections become `feedback_*.md` files, loaded at session boot, surfaced as standing rules with `**Why:**` and `**How to apply:**` context that lets the narrator generalize the rule.

The skill is intentionally heavy on persistence-to-disk. Working memory is unreliable. Disk is not.

## Example campaign structure

```
<memory>/
├── MEMORY.md              # index — always loaded, lightweight
├── feedback_pacing.md     # standing rule: transits 1-2 days
├── feedback_narration.md  # standing rule: director-led, no PC dialogue
├── project_<PC>.md        # PC canon
├── project_<NPC>.md       # NPC canon (one per recurring NPC)
├── project_<location>.md  # location canon
├── project_<threat>.md    # time-evolving threat state
├── economy/
│   ├── ledger.json        # finance state + history
│   └── (optional) history.json
└── state/                 # optional structured state for fleets, research, etc.
```

See [`examples/sample-campaign/`](examples/sample-campaign) for a populated starter.

## Tools (in `tools/`)

- `canon_check.py` — read entity file, return frontmatter + key sections for narrator prep
- `character_init.py` / `character_view.py` — PC / character file scaffolding + display
- `ledger_init.py` / `ledger_state.py` / `ledger_advance.py` / `ledger_deploy.py` — ledger lifecycle
- `state_init.py` / `state_view.py` / `state_advance.py` — operational state (fleets, research, locations)
- `registry_build.py` — build entity index from memory directory
- `save_memory.py` — manual memory-entry writer
- `common.py` — shared helpers

Each script is invoked directly with python. Most take `--memory-dir <path>` to point at the campaign.

## Hooks (in `hooks/`)

- `session_start.py` — fires on Claude Code session boot; loads campaign context into the conversation
- `stop_review.py` — fires after each assistant response; performs review checks (entity-name validation, suffix stripping, canon-cross-reference)

## Contributing

PRs and issues welcome — especially:
- New tool scripts for sub-systems the current ledger/state model doesn't cover well
- Improvements to the canon-check / audit logic
- Setting-specific feedback rules others have found valuable
- Documentation, examples, real-campaign transcripts (sanitized)

The skill is opinionated. Major design changes (e.g., replacing markdown canon files with structured DB, replacing the ledger with a different financial model) — open an issue first to discuss.

## License

MIT. See [LICENSE](LICENSE).

## Acknowledgments

Built and refined in the *Verse* campaign, a long-form sci-fi RPG run across many sessions with Claude Opus 4.7. The v1.1 audit-and-write-as-you-go rules were driven by a real audit that surfaced 8+ recurring NPCs and contracts living in transcript only after ~50 turns. The skill is opinionated *because* those opinions are forged from failure modes that actually happened.
