# Sample campaign — Veska, exiled scholar

This is a populated starter campaign meant as a reference for what a configured `claude-rpg-skill` memory directory looks like.

## Premise

**Veska** is a 24-year-old wandering scholar exiled from a scholarly order 14 months ago. She carries a **locked grimoire** she cannot open and is traveling east in the hope of finding a scholar who can. The Order is searching for her passively.

She is currently in **Brittle Hollow**, a small caravan-stop village in the borderlands. It is day 12 of the campaign. She has 47 silver, a traveling kit, and the book.

## How to use this

Either:

- **Copy** this directory into your own `~/.claude/projects/<id>/memory/` to start playing the Veska campaign immediately, or
- **Read** through the files to see the file structure, frontmatter conventions, `defer_to_user_on` discipline, ledger format, and `MEMORY.md` index style. Then build your own campaign with the same structure.

## What's modeled

- **A PC file** (`project_veska.md`) with a `defer_to_user_on` list — the canon facts the narrator will refuse to invent
- **A narrative-key asset** (`project_locked_book.md`) with deferred contents
- **A threat faction** (`project_the_order.md`) with established baseline + open intel timeline
- **A current location** (`project_brittle_hollow.md`) with NPCs at the level of detail they currently warrant (Maren and Doss have one-line sketches, not full bios)
- **Two standing rules** (`feedback_narration.md`, `feedback_updates.md`)
- **A populated ledger** with 6 days of history

## What's NOT modeled

- No combat system. No dice. No initiative.
- No deep faction politics yet — the Order is sketched at the level you need for early play.
- No state files (`state/`). The campaign is too small to need them yet.

## To play from this state

Invoke `/rpg` in a Claude Code session running with the skill installed and the memory directory pointed at this folder. The narrator will load Veska's canon and the ledger, then yield to you for the first action.
