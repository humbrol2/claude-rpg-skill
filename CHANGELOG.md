# Changelog

Newest first.

## v2.5 — 2026-10-10 — restructure for the current skill format

- **SKILL.md split.** Body is ~170 lines (was 556, over Anthropic's 500-line guidance). Failure modes, new-campaign setup, and session close-out moved to `reference/`; changelog to this file.
- **Frontmatter.** `disable-model-invocation: true` (RPG mode only on explicit `/rpg`), `argument-hint`, `allowed-tools` for the skill's own tools, and skill-scoped `hooks:` (Stop canon review, new PreCompact checkpoint). The Stop hook is no longer in `settings.json`; SessionStart stays there because it has to run before the skill is invoked.
- **Boot state is injected**, not fetched: `tools/boot_summary.py` runs at invocation via `!` dynamic context — canon integrity, ledger, threads, pressures, last beats with variety flag, checkpoint/last-session pointers. The SessionStart hook uses the same summary.
- **PreCompact checkpoint** (`hooks/precompact_checkpoint.py`): writes `sessions/checkpoint.md` (ledger line, tracking, last 4 narration turns) before every compaction in an RPG session. Boot reads it when `last_session.md` is missing. Pride II reached 389 beats without `/end` ever running; this closes that gap.
- **New tools.** `roll.py` (honest dice, `--adv/--dis`, natural 1/max flags), `ledger.py` (`show` / `post` / `tick` / `set-day` on the generic ledger schema; unknown top-level keys like `receivables` preserved and shown), `track.py` (`status` / `threads` / `pressures` / `beat` / `thread-*` / `pressure-*`; a beat bumps its threads in the same write), `canon_check.py --scene` (every file tied to a place, with its source line — the relationship-graph idea from claude-dnd-skill).
- **Sub-commands are skills.** `/rpg-status`, `/rpg-threads`, `/rpg-pressures`, `/rpg-canon`, `/rpg-roll`, `/rpg-check`, `/rpg-audit`, `/rpg-end` each live in their own directory with `argument-hint`.
- **Removed** the Verse-specific tools (`state_*`, `character_*`, `ledger_init/state/advance/deploy`) that the v2.0 changelog already declared phantom; the generic `ledger.py` replaces the ledger ones. `common.fmt_money` no longer exists.
- **Stop hook** unchanged in behaviour; `canon_ignore.txt` is now documented.

## v2.4

Hardening after a real canon-loss postmortem: a completed campaign's MEMORY.md carried 65 links into a directory outside the memory dir; when it was removed every reference dangled. Single-directory rule (failure mode #25); boot orphan check made blocking; duplicate step/failure-mode numbering fixed; tool paths made cwd-independent; SessionStart hook rewritten campaign-agnostic; frontmatter parser reads `type` under `metadata:`.

## v2.3

Failure modes #21 (economy windfall without friction) and #22 (ancient cache as default story gravity).

## v2.2

Boot loads `beat_log.json`, `threads.json`, `pressures.json`; beat log mandatory after every major beat; thread tracker with STALE at 100+ days; pressures tracker; NPC voice 5-point checklist; `/check` fun-signal command writing `feedback_live.md`.

## v2.1

Failure modes for formless supernatural beings and "presence" language as evasion.

## v2.0

Full rewrite. Removed phantom tool references and sci-fi-specific state; generic ledger; scene-opening, NPC-voice, resolution-mechanics, and consequence-tracking rules; failure modes #18–20.

## v1.9 and earlier

v1.9 new-playthrough robustness (`feedback_difficulty_variety.md` template, `sessions/`, session-1 warning). v1.8 blocking stub protocol, variety check, pre-scene failure check. v1.7 setup interview. v1.6 no easy mode. v1.5 registry check at boot and `/audit`. v1.4 time-skip tightening, PC autonomy, index↔ledger reconciliation. v1.3 PC name vs player name. v1.2 canon-check at locations, disambiguation, in-scene finance. v1.1 write-as-you-go, periodic audit.
