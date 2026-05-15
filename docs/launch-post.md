# Stop Your AI Narrator From Making Things Up

*A discipline framework for long-form RPG play with Claude — published alongside the [claude-rpg-skill](https://github.com/humbrol2/claude-rpg-skill) v1.1 release.*

---

I run long-form solo RPG campaigns with Claude. Months long. Same PC, same world, same recurring NPCs. The kind of arc where if the LLM forgets a name, gets a balance wrong, or invents a faction politics detail you didn't establish, the campaign starts to leak.

It always leaked. So I built a skill that stops it.

[**claude-rpg-skill**](https://github.com/humbrol2/claude-rpg-skill) is a Claude Code plugin that turns the model into a long-form RPG narrator with persistent canon, a structured finance ledger, and a set of operating disciplines that prevent the three failure modes that break every long-form LLM narration:

1. **Canon drift** — the model half-remembers and quietly fills in gaps
2. **Arithmetic slip** — credits move without explanation; balances don't reconcile
3. **Rule decay** — you correct the model; it forgets a week later

It is opinionated. It enforces discipline rather than offering options. That is the entire point.

## The three failure modes, concretely

### Canon drift

You introduce an NPC in turn 14. A 60-year-old retired captain named Vorrun. You describe him in three sentences.

By turn 80, the model has narrated Vorrun seven more times. Each time, it pulled a few facts from working memory, half-invented the rest, smoothed over inconsistencies. By turn 120, Vorrun is somehow 40 years old, has a daughter you never mentioned, and is fluent in a language you never established existed.

The model didn't lie. It compressed and approximated, which is what LLMs do under context pressure. Compression that's invisible turn-to-turn compounds catastrophically across hundreds of turns.

**The fix:** write a canon file for Vorrun the first time he speaks dialogue. Include a `defer_to_user_on:` list — the axes the narrator must NOT extrapolate on (his family, his prior career details, his languages, his personality beyond what's been shown). On every subsequent turn, before narrating Vorrun, the narrator reads his file. Facts not in the file or visibly established in transcript do not get invented. They get yielded back: *"I don't have that in canon — what would you like to establish?"*

### Arithmetic slip

You earn 3,640 credits. You spend 200 on dock fees. You earn 6,800 from another sale. You spend 915 on a refit. What's your balance?

If you're the player and you wrote it down: 9,325 credits, precisely.

If you're the LLM tracking it in conversational memory: depends what else has happened. Maybe 9,300. Maybe 9,200. Maybe 9,500 if it's been a long conversation and the model is doing its best.

By month two, you have no idea what your real balance is supposed to be. The number drifts whichever way the model's pattern-matching pulls hardest.

**The fix:** an append-only ledger in `ledger.json`. Every credit moved is a history entry with a day, a type, a delta, and a note. The narrator reads the ledger before stating any financial fact. When time advances, the narrator ticks the ledger forward (vehicle growth, weekly inflows, facility costs, standing policies) and reports from the updated state. Money never moves in narration without a corresponding ledger entry.

### Rule decay

You correct the narrator: *"transits are 1-2 days, not 4-5."* The narrator says *"got it."*

Three turns later, the narrator narrates a 6-day transit.

Why? Because the correction was a conversational acknowledgment, not a persistent change. Once the correction scrolls out of the model's active attention, it's gone.

**The fix:** corrections become `feedback_*.md` files in the campaign directory. Each one has a `**Why:**` line and a `**How to apply:**` line — the *reasoning* behind the rule, so the narrator can generalize it to edge cases instead of mechanically pattern-matching. The SessionStart hook loads every feedback file at session boot. Standing rules override default narration behavior, by design.

## The four disciplines

The skill encodes four operating disciplines that, together, prevent the failure modes above:

### 1. Canon-check before invoking named entities

Before narrating any named NPC, ship, location, or faction, the narrator consults the memory directory. If a canon file exists, it's read. Facts not in the file are not invented — they're yielded to the player.

### 2. Canon file write-as-you-go

This is the v1.1 rule that came directly out of running a real campaign for 379 in-game days and discovering, at audit, that eight recurring NPCs, several contracts, hidden assets, and threat-state evolutions were all living in transcript memory only.

When a new entity sticks in play — an NPC who has spoken dialogue, a contract with terms, a hidden asset, a comm protocol — a stub canon file is written **the same response**, not deferred to "session end." Session end may never come. Transcripts compress. Disk does not.

### 3. Ledger consultation before any financial fact

The narrator reads from `ledger.json`, not from working memory. Time advances? Tick the ledger. Decision made? Update the ledger. Reporting balance? Read the ledger.

### 4. Standing-rule overrides via `feedback_*.md`

Corrections become permanent rules with reasoning attached. The skill loads them at boot. They take precedence over default narration behavior. They survive across sessions.

## Periodic audit

Even with the above disciplines, things slip. Especially in a long campaign with many short turns. So the skill also runs a **periodic memory audit** — every ~15-20 turns, or on the player's explicit `/audit` invocation:

1. Have any named entities been introduced since the last audit that don't yet have files?
2. Are there contracts, agreements, or comm protocols living in transcript only?
3. Are there time-evolving canon facts being tracked in head rather than in a file?
4. Is `MEMORY.md` complete — every canon file linked?

This audit is what surfaced the eight-file gap on day 379 of my real campaign. The audit got formalized as a sub-command immediately afterward.

## Who is this for?

- **Solo TTRPG players** who want a GM that actually remembers
- **Long-form fiction collaborators** working with an LLM across many sessions
- **Anyone building** their own setting, NPCs, and arcs with an LLM as the co-narrator
- **People skeptical** that LLMs can hold a long arc — try this; it changes the game

It is *not* for:

- One-shots (overkill)
- Combat-heavy tactical play (no dice subsystem)
- Improv-friendly games where canon shouldn't matter

## Install and try it

Repo: [github.com/humbrol2/claude-rpg-skill](https://github.com/humbrol2/claude-rpg-skill)

Installation is one `git clone` into your Claude Code skills directory and one block added to `settings.json` to register the SessionStart hook. The README walks through it.

There's a populated sample campaign — **Veska, an exiled scholar carrying a locked grimoire** — that you can either play directly or read as a structural reference for building your own.

## What I want from you

**Critique.** Especially:

- Tool scripts that don't cover sub-systems you'd want them to
- Operating rules that miss failure modes I haven't hit yet
- Naming and structural decisions you'd argue against
- Real-campaign experiences (sanitized) where the skill helped or fell short
- Whatever you'd do differently

Issues and PRs welcome on the repo. The skill is v1.1; v1.2 is going to be informed by what other long-form players find when they put it to work.

## A note on the philosophy

I don't think LLMs are fundamentally bad at long-form narration. I think they're *un-disciplined* at it by default, and the discipline is something the surrounding system has to provide. Persistent memory, structured numerical state, explicit-override rules, periodic audits — these are well-understood disciplines from software engineering. The only novel part is applying them to a narrative co-author.

If this works for you, the next campaign you start with Claude will feel different. The model will remember. The math will stay clean. Your corrections will stick. The NPCs will stay who they were.

That is what playing alongside a serious collaborator feels like. The skill is here to make Claude one.

---

*Built and refined in a long-form sci-fi campaign run across many sessions with Claude Opus 4.7. Released MIT under [github.com/humbrol2/claude-rpg-skill](https://github.com/humbrol2/claude-rpg-skill).*
