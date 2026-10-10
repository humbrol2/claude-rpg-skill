# Failure modes

Every entry here was observed in live play. Each has a counter in SKILL.md. If one is about to happen, pause and ask the player rather than narrating through it.

## Contents
- Canon (1–3, 8–10, 12, 17–19, 25)
- Money and time (4, 6, 11, 13, 21)
- Narration and stakes (5, 7, 14–16, 20)
- Genre autopilot (22–24)

## Canon

1. **Inventing NPC histories** — canon-check before invoking each name.
2. **Campaign naming conventions ignored** — check `feedback_*.md` / `RPG_CAMPAIGN.md` for how to parse names (honorifics, suffixes) before lookup.
3. **Read-in violations** — outer-circle NPCs knowing inner-circle facts. Check `read_in_tier` before a character narrates knowledge.
8. **Transcript-only canon** — NPCs, contracts, consequences introduced in play but never filed. Write stubs as you go.
9. **Novelty-default at established locations** — inventing a new hook instead of grounding the scene in existing canon. Run `canon_check.py --scene` and lead with what's known.
10. **Silent disambiguation** — picking one canon entry when the reference matches multiple. *"Two fit — A or B?"*
12. **PC-vs-player name conflation** — using the player's real name in scene. The drift is gradual: the player signs prompts with their name, and the narrator slides into it.
17. **Deferred NPC stubs** — NPC speaks, session continues, stub never written. Blocking: stub before the next narration beat.
18. **NPC voice collapse** — all NPCs sounding like a helpful narrator summarising their position. Read the file, find their agenda, write from inside it.
19. **Missing consequence filing** — a fight is won, a relationship shifts, a faction is alerted, and nothing is written. World-state changes need files, not just NPC stubs.
25. **Cross-directory canon links** — `MEMORY.md` linking via `../` or into another directory tree. Breaks silently when anything moves; a completed campaign once lost 65 entity files this way, leaving one-line index descriptions as the only surviving canon. All campaign files live in the memory directory; links are bare filenames. The boot orphan check is the tripwire — never narrate past DANGLING.

## Money and time

4. **Numerical drift** — liquid moving without a ledger entry. `ledger.py post` for every transaction.
6. **Time-skip overshoot** — multi-week jumps when the player expected a week. Ceiling is 7 days per response.
11. **Narrative-only finance** — narrating a payment and reporting the pre-payment balance three lines later. Post first, report from the ledger.
13. **Index↔ledger drift** — narrating from `MEMORY.md`'s state when the ledger has advanced past it. Reconcile at boot; ask, don't pick.
21. **Economy windfall without friction** — a single find (ore seam, cache, exploit) that would 10× liquid in one session. Before the money lands, at least one of: a buyer who asks about origin, faction attention from unusual volume, a logistical limit on extraction speed, a rival who noticed too. Windfalls are earned through risk management, not automatic conversion.

## Narration and stakes

5. **Standing-rule decay** — feedback corrections fading mid-campaign. Re-read all `feedback_*.md` at every boot.
7. **PC dialogue intrusion** — narrating the PC's words in major scenes. Hand the floor over.
14. **PC-autonomy overreach** — narrating the PC's solo time, interior, unstated actions, or downtime initiative.
15. **Easy-mode narration** — railroading to success, retroactive rescues, plot armor, telegraphed safety.
16. **Beat-type monotony / "make friends" default** — every session dominated by social beats, every NPC becoming an ally. Run the beat-type check before each major scene; NPCs have the standing to refuse.
20. **Pre-decided outcomes** — deciding the PC will succeed, then framing the attempt as uncertain. If it was decided, drop the uncertainty framing; if it's uncertain, roll first.

## Genre autopilot

22. **Ancient cache as default story gravity** — buried structure → artifact on a plinth → responds to touch → visions → network of sites → grand legacy. The default for any buried find is mundane: a storage cache, an equipment depot, a supply room. Supernatural properties need explicit player direction. Ask *"what would this actually be if the world were realistic?"* before reaching for the mythic. Ancient ≠ significant. Sealed ≠ chosen.
23. **Formless supernatural beings** — introducing an entity by what it *feels like* rather than what it *is*. Every being has form: body, face, shape, voice, identifiable nature. Atmospheric language is for first contact across a threshold only. Three scenes with no form is a failure.
24. **"Presence" language as evasion** — "a presence", "a texture", "a quality of attention", "something at the edges", "vast awareness" used instead of characterisation. Yellow flags after first contact. If you cannot describe what it looks like, you have not finished making it.
