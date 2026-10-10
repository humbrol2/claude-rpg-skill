# New campaign setup

Trigger: boot finds no campaign, or the player says "new campaign". Create a fresh memory directory; never overwrite existing campaign files.

## Contents
- Setup interview (one pass)
- Scaffold
- `feedback_difficulty_variety.md` template
- Single-directory rule
- Session-1 pattern warning

## Setup interview

Ask all of these in a single message. Do not invent answers; record anything left open as *"TBD — establish in play."*

1. **Setting & tone** — genre, world, era, mood.
2. **Rules system** — D&D 5e, Call of Cthulhu, Blades in the Dark, custom, or "no system, resolve by fiction." Fixes how uncertainty resolves for the whole campaign.
3. **PC** — in-fiction name (distinct from the player's own), concept, starting location. Confirm explicitly which name is which.
4. **Stakes dial** — is PC death on the table? Which consequences are live: injury, money, reputation, relationships, heat, sanity.
5. **Story variety** — beat types to emphasise or avoid. Defaults by genre:
   - Fantasy: social, combat, travel, intel, arcane, economic, personal
   - Sci-fi: social, combat, travel, intel, technical, economic, personal
   - Crime/noir: social, investigation, action, surveillance, negotiation, heat, personal
   - Custom: define them and note them in `feedback_difficulty_variety.md`

   NPCs do not auto-ally by default; adjust only if the player explicitly wants a warm social campaign.
6. **Pacing & autonomy** — confirm the defaults (1–3 day skips, one-week ceiling, narrator yields the PC's words and interior) or adjust.
7. **Economy** — currency, starting liquid, recurring income/outflows. May be "establish in play."
8. **Opening scene** — where and how we begin.

## Scaffold

Confirm the file list with the player, then create inside the memory directory:

- `RPG_CAMPAIGN.md` — `memory_dir: <absolute path>` plus a short boot summary; optional `ignore_names: Stealth, Perception` for rules terms the Stop hook should not flag
- `MEMORY.md` — index seeded with setting summary, PC link, standing-rule links, empty threads list
- `project_pc.md` — the PC's canon file
- `feedback_stakes.md` — from item 4
- `feedback_difficulty_variety.md` — from item 5, using the template below
- `feedback_pacing.md`, `feedback_pc_autonomy.md` — from item 6
- `sessions/` — empty; `beat_log.json` and `threads.json` are created by `track.py` on first write
- `economy/ledger.json` — from item 7; `as_of_day` is the integer 0

```json
{
  "as_of_day": 0,
  "currency": "<name and conversions>",
  "liquid": {"<denomination>": 0},
  "assets": [],
  "monthly_inflows": [],
  "monthly_outflows": [],
  "history": [{"day": 0, "type": "initialization", "delta": "Starting purse X.", "actor": "narrator"}]
}
```

## `feedback_difficulty_variety.md` template

This file is load-bearing. If it is ever missing or DANGLING, recreate it from here before narrating.

```markdown
---
name: difficulty-variety
description: Story variety and difficulty enforcement for this campaign.
type: feedback
---
# Difficulty & Variety

**Difficulty dial:** [player's answer]
**Beat types for this genre:** [list]
**Beat-type emphasis:** [player's answer, or "rotate evenly"]
**Beat-type avoid:** [player's answer, or "none"]

## Active anti-patterns (always enforced)
- NPCs do not automatically become allies. Indifference, refusal, and hidden agendas are the default.
- Plans are attempts, not results. Name the failure state before narrating any challenge.
- The world does not arrange convenient rescues. No retroactive plot armor.
- Session health signal: if the PC has faced no genuine cost in 10+ turns, introduce a complication.

## Beat-type check
Before each major beat, identify the last 3 beat types (`track.py status`).
If 2+ of the last 3 are the same type and the player hasn't pushed that direction, vary.
```

## Single-directory rule (hard requirement)

Every campaign file — canon, feedback, sessions, economy — lives inside the memory directory. `MEMORY.md` links are bare filenames or subdirectory paths, never `../` and never another drive or tree. A cross-directory link breaks silently the moment either side moves. If the player wants canon visible in a project folder, put the *campaign* there and point `RPG_CAMPAIGN.md` at it.

## Session-1 pattern warning

The first 3–5 turns set habits that persist for hundreds of sessions:

- The first NPC sets the tone. Not warm, not helpful, not allied by default. Give them their own agenda.
- The first challenge sets the stakes dial. Resolve it honestly; don't soften it to ease the player in.
- The first stub file sets the canon-hygiene habit. Write it immediately.

Then surface the ready message and open on the scene from item 8.
