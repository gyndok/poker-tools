# Design: No-install "lite" path for poker-hand-review

**Date:** 2026-06-23
**Status:** Approved (pending spec review)
**Repo:** github.com/gyndok/poker-tools

## Problem

A poker player who finds the launch tweet may have no Claude account and no
experience with skills/plugins or GitHub. The existing product (the
`poker-hand-review` plugin) reads hand-history files off disk and runs Python,
so it **requires Claude Cowork or Claude Code** — a desktop/terminal install
plus folder connection. That app-install floor is the main drop-off point for a
cold tweet-clicker. No amount of landing-page copy removes it.

The only way under that floor is a **different, zero-install path**: plain
`claude.ai` chat where the player uploads one hand-history `.txt` and gets a
review. No app, no plugin, no GitHub, no folder connection.

## Goal

Add a no-install "lite" on-ramp that:
- works in plain `claude.ai` chat (free account is enough),
- needs only a single pasted/clicked prompt + one uploaded `.txt`,
- preserves the house style of the full skill (blunt GTO, ICM/stack-depth),
- does **both** hand-by-hand review **and** a lightweight stats read (with a
  loud small-sample caveat),
- becomes the **primary** CTA for newcomers, with the plugin demoted to the
  "power user / whole archive" path.

## Non-goals

- The lite path does **not** run Python; stats are counted by hand from one
  uploaded file and are explicitly directional, not authoritative.
- It does not read the disk or scan a whole archive — that stays the plugin's
  job and is the upgrade hook.
- Not changing the plugin or its scripts.

## Decisions (locked during brainstorming)

1. **Delivery = both** ("C"): a one-click **Open in Claude** button *and* a
   copy-paste prompt block, driven by the same prompt text. Button for speed,
   copy block as the no-length-limit fallback.
2. **Scope = both** ("A"): hand-by-hand review **and** a lightweight stats read
   (VPIP/PFR/3-Bet/C-Bet/WTSD + style label), prefaced with a loud
   "one small session, directional only, I may miscount on a hand count" caveat.
3. The lite path still requires the player to upload an ACR/WPN hand-history
   `.txt`; the page includes a 2-line "how to get your file" note.
4. GitHub Pages enabled via API (maintainer convenience), serving from `/docs`.

## Components

### 1. `lite/coach-prompt.md` (canonical prompt — single source of truth)

A self-contained prompt, target **≤ ~1,800 characters** so it has a real chance
of fitting the one-click URL. Condensed faithfully from
`plugins/poker-hand-review/skills/poker-hand-review/SKILL.md`. Must include:

- **Role + input:** blunt GTO poker coach; the player will attach an
  America's Cardroom / WPN tournament hand-history `.txt`; hero = the player in
  the `Dealt to <name>` lines; ask for the screen name if ambiguous.
- **Blunt-tone rule:** name leaks as mistakes, don't cushion, but a cooler is
  not a leak — distinguish variance (ran bad) from EV loss (a mistake).
- **Per-hand review:** setup line (level/blinds+ante, position, exact hand,
  stack in chips and BB) → action recap with bet sizes as % of pot and board per
  street → street-by-street GTO verdict → ICM & stack-depth adjustment → one
  bolded takeaway.
- **Workflow:** list the hands the hero did not fold preflop, then review one at
  a time; "next" continues in order.
- **Stats read:** compute VPIP / PFR / 3-Bet / C-Bet / WTSD by hand from the one
  file; present a small "you vs typical TAG vs read" table + play-style label;
  **lead with the small-sample caveat**; do not hard-diagnose a leak off a tiny
  stat — point to the hand-by-hand evidence instead.
- **Honesty:** GTO-*principle* analysis, not a solver run; never invent cards,
  sizes, or results not present in the text; flag uncertainty.

If the prompt cannot be trimmed to a URL-safe length without losing fidelity,
the **copy block is the source of truth and the button degrades gracefully**
(see verification below).

### 2. Landing page `docs/index.html`

Start from the existing landing page (currently the standalone
`poker-start-here.html` in session outputs; it embeds the sample-card PNG so it
is a single self-contained file). Restructure the top into a two-path fork:

- **"Try it free — no install (30 sec)"** → the lite section:
  - **Open in Claude** button → `https://claude.ai/new?q=<url-encoded prompt>`
  - **📋 Copy the coaching prompt** → same text to clipboard
  - one-line "how this works": free Claude account is enough; no app/plugin/
    GitHub; best with one tournament file at a time
  - 2-line "how to get your hand-history file" note (turn on hand-history
    saving in the ACR client; the file is `HH….txt`)
- **"Want your whole archive + exact stats?"** → the existing plugin install
  (Cowork/Claude Code), demoted to the power-user path.

The button URL and the copy-block text are both generated from the **same**
prompt string so they never drift.

### 3. Publish

- Commit `lite/coach-prompt.md` and `docs/index.html`; push to `main`.
- Enable GitHub Pages via API, source = branch `main`, folder `/docs`.
- Live at `https://gyndok.github.io/poker-tools/`.

### 4. Tweet tweak

Reframe "stats" so the free path does not over-promise:
"…plus a quick stats read in the free version (full tracker stats with the
plugin)." Final copy out of scope for this repo; noted for the maintainer.

## Data flow

```
tweet → gyndok.github.io/poker-tools (docs/index.html)
  ├─ "Open in Claude"  → claude.ai/new?q=<coach prompt> → user attaches HH*.txt → review + stats
  └─ "Copy prompt"     → paste into new claude.ai chat   → user attaches HH*.txt → review + stats
  └─ "whole archive"   → /plugin marketplace add gyndok/poker-tools (Cowork/Code)
```

## Verification

- **URL length:** after writing the prompt, URL-encode it and confirm the
  `claude.ai/new?q=` link loads and pre-fills on a logged-in session. If it
  truncates, keep the button but add a note that the copy block is the complete
  version, and/or trim the prompt. Record the result.
- **Prompt fidelity:** diff the lite prompt's coverage against SKILL.md's
  tone/stats/ICM sections — every named behavior above is present.
- **Page integrity:** `docs/index.html` opens offline (PNG still embedded), both
  buttons work (button navigates to the encoded URL; copy puts the full prompt
  on the clipboard), and no broken external links except the intended GitHub +
  claude.ai links.
- **Pages live:** `https://gyndok.github.io/poker-tools/` returns 200 and shows
  the new fork.

## Open risks

- Hand-counted stats on <100 hands are noisy and Claude can miscount; mitigated
  by the mandatory caveat and by pointing to hand-by-hand evidence over the
  numbers.
- `claude.ai/new?q=` behavior/length cap is not contract-guaranteed; the copy
  block is the durable fallback.
