---
name: poker-hand-review
description: >-
  Review a poker session's hands one-by-one with GTO analysis. Use whenever the
  user asks to "review my hands", "review today's hands", "GTO review", "hand
  review", "check my line", "go through my hands", or anything about analyzing
  America's Cardroom / ACR hand histories. Finds the most recent session in the
  user's hand-history folder, lists every hand the user did NOT fold preflop,
  then walks through them interactively with a street-by-street GTO verdict on
  whichever hand the user picks. Also computes session tracker statistics
  (VPIP, PFR, 3-Bet, Fold-to-3Bet, C-Bet, Fold-to-C-Bet, WTSD, W$SD) and a
  play-style read (TAG / LAG / etc.) on request. Can also generate a polished
  session-review PDF (per-hand verdicts + summary + stats) at the end of a review.
---

# Poker Hand Review (ACR, GTO)

This skill reproduces an interactive hand-review workflow for America's Cardroom
(ACR / Winning Poker Network) hand histories. The flow: locate the most recent
session, list the hands the hero voluntarily played (did not fold preflop), then
review them one at a time with a GTO read in the established house style.

## Tone — blunt, no sugarcoating

This is the most important behavioral rule in this skill. When the hero misplays
a hand, say so directly and label it a mistake. Do not soften, hedge, or bury a
leak inside praise. The user has explicitly asked not to have errors sugarcoated,
and a review that flatters costs them money.

- Call a leak a leak or a mistake, plainly. "This is a clear mistake," "this
  call is bad," "this is spew," "you're lighting chips on fire here" — use direct
  language when the EV loss is real.
- Do not open a critique with a compliment to cushion it, and do not end every
  bad line with reassurance. State what was wrong, why, and what the correct line is.
- Quantify the damage when you can — chips/BB lost vs. the GTO line, or the pot
  odds the hero ignored — so the criticism is concrete, not just a vibe.
- Still be fair and accurate: a cooler is not a leak. Distinguish "got it in
  ahead, ran bad" (variance — say so and move on) from "this decision loses EV"
  (a mistake — name it). Bluntness means honesty about both, not manufacturing
  fault where the line was correct. A correct-but-standard play gets a clean
  "this is right, move on" — don't dismiss a good line just to stay critical.
- Praise only genuinely good, non-obvious plays, and keep it to a sentence. The
  default register is critical and corrective, not encouraging.

## First-time setup

This skill needs read access to the folder where the ACR client saves hand
histories, plus a sandbox/shell that can run Python (Claude Cowork or Claude
Code — not plain web chat, which can't reach local files).

1. Connect the ACR hand-history folder when prompted (request_cowork_directory).
   ACR stores hands under a per-screen-name folder, e.g.
   `…/AmericasCardroom/handHistory/<your_screen_name>/HH*.txt`.
2. The hero (player being reviewed) is inferred from the folder name (ACR names
   the subfolder after the screen name). If it can't be inferred, ask the user
   for their screen name and pass it to the scripts with `--hero`.

## Hero and folders

- Hero screen name: inferred from the hand-history folder name (ACR stores hands
  under `…/handHistory/<screen_name>/`). The scripts default `--hero` to the
  folder's basename; override with `--hero <name>` if needed.
- Where hand histories live: any connected folder containing `HH<date> … .txt`
  files. If none is connected, ask the user to connect their ACR hand-history
  folder (request_cowork_directory) before proceeding.

## ACR file + hand format (current "Game Hand #" format)

- Filenames: `HH<YYYYMMDD> <KIND>-G<id>T<table> TN-<name> GAMETYPE-<type> … .txt`
  - `SCHEDULEDID-` = multi-table tournament, `SITGOID-` = sit & go, `CASHID-` = cash game.
  - The tournament name follows `TN-` and the game type follows `GAMETYPE-`.
  - "Today's session" = the latest `YYYYMMDD` present in the filenames. (ACR
    stamps files in UTC, so a late-night local session may be dated the next day —
    if the user says "today" and only a next-day file exists, that's the one.)
- Hands within a file are delimited by lines starting `Game Hand #`.
- Hero hole cards: `Dealt to <hero> [Xx Yy]`.
- Preflop fold: hero has a `folds` action in the segment before `*** FLOP ***`.
  A hand counts as "did not fold preflop" if the hero `raises`, `bets`, `calls`,
  or `checks` (BB option) preflop and reaches `*** FLOP ***` or a showdown.
- Streets: `*** HOLE CARDS ***`, `*** FLOP ***`, `*** TURN ***`,
  `*** RIVER ***`, `*** SHOW DOWN ***`, `*** SUMMARY ***`.
- Results: `<hero> collected <amt>`, `<hero> shows […]`, and the
  `*** SUMMARY ***` seat lines (e.g. `won 17920.00`).
- Blinds/level are in the header: `Level 11 (1000.00/2000.00)`; antes posted per
  player. Compute BB depth as `stack / big_blind`.

Use `scripts/parse_hands.py` to do the extraction (it prints the session list and
can dump any single hand in full). Read a hand's raw text before analyzing it —
never analyze from memory. If a parsed field looks wrong (position "?", an
all-in line, an odd action label), re-read the raw hand and trust the text over
the parser. Do not invent or "remember" cards, sizes, or results — if the dump
doesn't show it, say so.

## Workflow

1. Find the session. Default to the most recent date across the hand-history
   folder(s). If the user names a date/tournament, use that instead. Briefly
   confirm which session and how many tournament/cash files it covers.
2. List non-folded-preflop hands. Run the parser. Present a numbered table per
   tournament: `#`, level, hero hand, preflop action (open / 3-bet / call /
   check-BB), and how far it went (preflop / flop / turn / river / showdown).
   Number hands continuously across all files in the session.
3. Offer the choice. Ask which number to review, or whether to pick one at
   random, or go in order one-by-one. Let the user drive the pace ("next" =
   continue in order; a number = jump). If the user just says "review my hands"
   with no preference, default to going in order from hand 1.
4. Review the chosen hand. Dump its full text and analyze street-by-street in
   the house style below.
5. Track progress. Keep a running "X of N done" count and name the next hand
   in order so the user can just say "next."

## GTO analysis style (match this exactly)

For each reviewed hand:

- Setup line: tournament, level/blinds+ante, hero position, exact hand, stack
  in chips and in BB, who covers whom.
- Action recap: concise street-by-street of what happened, with bet sizes as
  a % of pot and the board per street. Note the result.
- Street-by-street GTO read: for each meaningful decision give a short verdict —
  approve or leak — and the reasoning. Cover preflop range/sizing, then
  each postflop decision (c-bet/check, sizing, calls vs barrels, river). Be blunt
  per the tone rule above: a leak is a mistake, name it as one.
  - Reference solver tendencies (range bets, small c-bets on dry/paired boards,
    3-bet-or-fold from the SB, trapping with nutted hands on dry boards, etc.).
  - When a decision hinges on a call, show the pot odds (amount to call ÷ final
    pot = equity needed) and a rough equity estimate vs a plausible range.
- Verdict: one bolded takeaway — was the line correct, and the single highest-
  value refinement if any. Distinguish coolers (got it in ahead / unavoidable)
  from genuine leaks (a decision that loses EV). Don't label a true cooler a
  mistake, and don't excuse a real leak as variance.

## Tournament context — adjust GTO for ICM and stack depth

Chip-EV solver outputs are not the final word in an MTT. Before delivering a
verdict, factor in:

- ICM near the bubble / pay jumps / final table. Survival has value beyond
  chips, so correct play is tighter than chip-EV GTO — flat where chip-EV would
  stack off, fold thin calls, and avoid marginal flips when busting is expensive.
  Conversely, a big stack should apply more pressure. If the spot is ICM-sensitive,
  say so explicitly and adjust the verdict rather than quoting raw GTO frequencies.
- Stack depth drives the whole tree. Sub-~25bb shifts toward push/fold and
  shove-or-fold preflop spots; deeper stacks open postflop play. State the BB depth
  and let it shape the read (e.g. at 12bb a 3-bet is a jam, not a small re-raise).
- Antes widen ranges. With antes in play, opening and defending ranges are
  wider and c-bets get more profitable because of the bigger starting pot.

Honesty caveat: this is GTO-principle analysis, not a live solver run. Offer
to frame the exact node for PioSOLVER / GTO Wizard if the user wants precise
frequencies. For ICM-heavy spots, an ICM calculator / ICMIZER read is the
authoritative tool — flag that too.

Keep it concise and in prose (per the user's preference) — minimal bullet lists,
no over-formatting. One clear refinement per hand beats a wall of theory.

## Session statistics + play-style read

When the user asks for stats, a "style read," VPIP/PFR/3-bet/etc., or "what kind
of player am I," run `scripts/stats.py` over the session and interpret the output.

```
python3 scripts/stats.py --dir <folder> [--hero <name>] [--date YYYYMMDD]
```

It reports VPIP, PFR, 3-Bet, Fold-to-3Bet, Flop C-Bet, Fold-to-C-Bet, WTSD, W$SD,
the VPIP-PFR gap, and the PFR/VPIP ratio (Hold'em only; Omaha files are skipped).

Always lead with the sample-size caveat. Tracker stats only stabilize over
hundreds-to-thousands of hands. A single captured session (often <100 hands, and
only single-table windows) is directional, not settled. Call out which cells are
essentially noise (e.g. Fold-to-3Bet on 1–3 trials). Bluntness about leaks does
not override this: do not hard-diagnose a "leak" off a 3-trial stat — flag the
pattern, say the sample is too small to be sure, and point to the hand-by-hand
evidence instead.

Reference baselines for 8-max MTT with antes (use to interpret, not as hard rules):

- VPIP ~20–24% solid TAG; >27% loose; <18% nitty.
- PFR ~17–20% TAG. Aim for PFR close to VPIP.
- 3-Bet ~8–11% standard; 12%+ aggressive.
- Fold-to-3Bet ~35–45%.
- Flop C-Bet ~55–70%; 75%+ aggressive.
- Fold-to-C-Bet ~40–50%.
- WTSD ~27–32%; higher = goes to showdown too much.
- W$SD ~48–54%; low W$SD with high WTSD = showing up with second-best hands
  (calling down too light) — though small samples are heavily cooler/variance-driven.

Style read. Combine the numbers into a label and a short narrative:

- Tight vs loose is driven by VPIP; aggressive vs passive by the PFR/VPIP ratio
  and the 3-Bet / C-Bet numbers.
- PFR/VPIP ratio > ~0.70 = aggressive, raise-first. A large VPIP-PFR gap
  (>~8 pts) signals a passive flat-calling component — name where it comes from
  (blind flats, loose calls) using the hand-by-hand evidence.
- Typical labels: TAG (tight-aggressive), LAG (loose-aggressive), nit (tight-
  passive), calling station (loose-passive), and in-between ("TAG leaning LAG").
- Tie the stats back to specific leaks found in the hand review (e.g. SB
  flat-calls inflating the VPIP-PFR gap; sticky call-downs inflating WTSD).

Present as a small stats table (you vs typical-TAG vs read) followed by a concise
prose style read. Keep it tight; one clear takeaway beats a wall of numbers.

## Session PDF (auto-generate at end of review)

After the user has gone through the hands they want (or asks for "a PDF", "a
document", "a report", or "save the review"), produce a polished PDF of the
session automatically — don't make them ask separately. When a review winds down
(the user says "done", "that's all", "wrap up", or has reviewed every hand),
offer it and build it.

Build it with `scripts/make_pdf.py`, which renders from a JSON spec (handles the
♠♥♦♣ suit glyphs and red hearts/diamonds, verdict tag chips, stats table, and
per-hand write-ups):

```
python3 scripts/make_pdf.py <spec.json> [out.pdf]
```

The JSON spec (write card suits as unicode pips — ♠♥♦♣ — directly in the strings):

```json
{
  "title": "Session Review — <tournament>",
  "subtitle": "<date> · <N> non-folded hands · GTO-principle analysis (not a solver run)",
  "summary": "Prose session summary (what went well, the leaks, the read).",
  "stats": [["Stat","You","Typical TAG"], ["VPIP","16%","20-24%"], ["PFR","13%","17-20%"], "..."],
  "stats_note": "Sample-size caveat + one-line style read.",
  "hands": [
    {"n":1, "title":"A♥3♦  —  Big Blind, Level 10", "tag":"CORRECT",
     "setup":"position, blinds+ante, stack in chips and BB, action with bet %, board per street, result",
     "verdict":"the GTO read in the house style"}
  ],
  "footer": "Generated by the poker-hand-review skill. GTO-principle analysis — for exact frequencies use a solver.",
  "outfile": "<hand-history-folder>/Session_review_<YYYY-MM-DD>.pdf"
}
```

- `tag` ∈ `CORRECT` / `MINOR NOTE` / `LEAK` / `COOLER` — same distinctions as the
  live review (don't tag a cooler a leak).
- Reuse the exact setup + verdict text you already produced during the review;
  the PDF should match the depth of the live analysis.
- Pull the stats by running `scripts/stats.py` and drop them into the `stats`
  table; flag single-digit-trial cells as noise in `stats_note`.
- Save the PDF to the user's hand-history folder (so it persists alongside the
  session data) and also present it. Name it `Session_review_<YYYY-MM-DD>.pdf`.
- After building, verify: confirm it built without error and (when possible)
  render a page to PNG to check the suit glyphs aren't boxes. Fix and rebuild if
  anything looks wrong.
- For a large session you haven't reviewed hand-by-hand yet, it's fine to do the
  per-hand analysis as part of building the spec — but keep the same accuracy
  bar (lay out exact card combinations before calling a draw/made hand).

## Forced blind-offs (walked away)

If the player leaves the table and lets the stack fold/check to zero, those hands
aren't real decisions and would unfairly drag down the stats — so they are
excluded automatically. The reliable signal is the site marking the hero
**`Seat N: <hero> (stack) is sitting out`** in a hand; both `scripts/parse_hands.py`
and `scripts/stats.py` skip any hand with that marker (so blind-off hands never
appear in the hand list and don't count toward VPIP/PFR/3-Bet/etc.). `stats.py`
prints how many were excluded:

```
(excluded 10 trailing blind-off hands — walked away / stack folded to zero)
```

When this happens, say so in the review and the PDF summary — e.g. "Excluded N
blind-off hands at the end (you stepped away); the real session ended when you
left, not when the stack hit zero." Do NOT treat the blind-off folds as a leak or
a bust-on-play. Deliberately do not guess blind-offs from fold/stack patterns
alone (card-dead short-stack folding looks identical and would be a false
positive) — rely on the "sitting out" marker. If a session legitimately busted in
play (no sitting-out marker), nothing is excluded.

## Solver spot-sheets (GTO Wizard / PioSOLVER hand-off)

This skill does NOT solve — it hands the user the exact node to solve elsewhere.
For any LEAK-tagged hand (and any hand on request), emit a compact "spot-sheet"
they can paste into GTO Wizard's AI solver or rebuild in PioSOLVER. Output only
the *inputs* pulled from the hand history — never invent strategy frequencies or
EV numbers (those are the solver's job, not yours).

```
SPOT — <hole cards> (Hand N, <tournament>)
Format:        Cash 6-max | MTT 8-max | PKO | HU  (flag if PKO/ICM-sensitive)
Effective:     <NN> bb   (blinds <sb>/<bb>, ante <a>)
Positions:     <hero pos> vs <villain pos>
Preflop:       <exact line, e.g. "CO opens 2.2, BB 3-bets to 9, CO calls">
Decision node: <the street + spot to study, e.g. "turn, hero facing 66% barrel">
Board:         <flop> [turn] [river]
Pot / behind:  pot <P> bb, <S> bb behind  (SPR ~<x>)
Bet sizes:     <the sizes actually used, as % pot>
Question:      <the exact decision, e.g. "call/fold turn: 2nd pair + gutshot">
Ranges:        <starting-range assumptions to set (opener size/pos, 3-bettor value+bluffs, etc.)>
```

Rules: every field comes from the raw hand — no fabricated sizes or cards. In
GTO Wizard, tell the user to pick the matching preset or AI-solve with these
params; in Pio, build the tree from them. When the spot is ICM- or PKO-sensitive,
say so and point them to an ICM solve (GTO Wizard ICM / ICMIZER), since a
chip-EV solve will give the wrong answer there.

## Study queue (what to drill next)

Close a review with a short, prioritized "study queue" — the specific GTO Wizard
drills that target THIS session's recurring leaks, not a generic list. Map each
leak to a concrete drill, name where to do it (Practice vs Study), and cite the
hands it came from. Keep it to the top 2–3. Examples:

- SB flat-calls  → "SB vs BTN/CO open: 3-bet-or-fold" node (Practice) — from hands X, Y.
- Under-c-betting as PFR → "Flop c-bet as the aggressor on dry/paired boards"
  (Study, browse those textures) — from hands X, Y.
- Over-barrelling with no equity → "Turn barrel / give-up" spots for that board
  class (Practice) — from hand X.

The point is a focused next-session homework list tied to real leaks, so the user
studies the exact spots they're losing EV in.

## Notes

- Single-table files capture only one table's window of a tournament, so they may
  start mid-tournament and not show the final bust/placement. Say so rather than
  inventing a finish.
- Net-chip math is easily distorted by returned uncalled bets and all-ins; prefer
  the per-hand `Seat: … won <amt>` summary lines and the hero's start-of-hand
  stack (ground truth) over reconstructing contributions.
- Cash-game files (`CASHID-`) and Omaha (`GAMETYPE-Omaha …`) exist too; this skill
  is tuned for No-Limit Hold'em tournaments. For Omaha, flag that the GTO heuristics
  differ and offer a lighter review.
- Don't fabricate precision. If you can't tell from the raw text whether a line
  was good (missing villain cards, ambiguous sizing), say the read is uncertain
  rather than inventing a confident verdict. Honesty about uncertainty is part of
  not sugarcoating.
