# Poker Lite Path Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a no-install "lite" on-ramp so a cold tweet-clicker can get a poker hand review in plain claude.ai chat (free account, no app/plugin/GitHub), with the plugin demoted to the power-user path.

**Architecture:** A single canonical coaching prompt (`lite/coach-prompt.md`) is embedded into the landing page (`docs/index.html`) as one JS string that drives both a one-click `claude.ai/new?q=…` button and a copy-to-clipboard block. The page is published via GitHub Pages (`main` branch, `/docs` folder). No changes to the existing plugin.

**Tech Stack:** Static HTML/CSS/JS (no build step), `gh` CLI + GitHub REST API, git.

**Working branch:** `feat/lite-path` (already created, spec already committed).

---

## File Structure

- Create: `lite/coach-prompt.md` — canonical coaching prompt, the single source of truth for the prompt text.
- Create: `docs/index.html` — landing page (copied from the existing standalone `poker-start-here.html`, then extended with the lite section). Self-contained (sample-card PNG stays embedded).
- (No other source files; the plugin under `plugins/` is untouched.)

The prompt text exists in two places by necessity (the `.md` for humans, a JS string in the HTML for the buttons). Task 3 copies the exact text from the `.md` into the HTML and adds a "keep in sync" comment so they don't drift.

---

## Task 1: Author the canonical lite coaching prompt

**Files:**
- Create: `lite/coach-prompt.md`

- [ ] **Step 1: Write the prompt file**

Create `lite/coach-prompt.md` with EXACTLY this content (the body below the marker line is the prompt that gets pasted into claude.ai):

```markdown
# Lite coaching prompt

This is the canonical text for the no-install "lite" path. It is pasted into a
fresh claude.ai chat (or pre-filled via the "Open in Claude" button on the
landing page). Keep `docs/index.html`'s `POKER_COACH_PROMPT` string in sync with
the body below.

---

You are a blunt, no-sugarcoating GTO poker coach. I'll attach an America's Cardroom / Winning Poker Network tournament hand-history .txt. The hero (me) is the player named in the "Dealt to <name>" lines — if that's unclear, ask my screen name before analyzing.

Tone: name leaks as mistakes, plainly ("this is a clear mistake," "this is spew"). Don't cushion criticism with compliments. But a cooler is not a leak — separate "got it in ahead, ran bad" (variance, move on) from "this decision loses EV" (a mistake). Praise only genuinely good, non-obvious plays, in one sentence.

Do this:
1) List every hand I did NOT fold preflop, numbered, with level/blinds, my position, my hand, my preflop action, and how far it went. Then review them one at a time; when I say "next," continue in order.
2) For each hand: a setup line (level/blinds+ante, position, exact hand, stack in chips and BB, who covers); a street-by-street action recap with bet sizes as % of pot and the board; then a blunt GTO verdict per decision (preflop range/sizing, c-bet/check, calls vs barrels, river). Show pot odds when a call is close. Adjust for ICM and stack depth — pay jumps/bubble mean tighter than chip-EV, sub-25bb is push/fold, antes widen ranges. End with one bolded takeaway.
3) When I ask for stats, count VPIP, PFR, 3-Bet, C-Bet, and WTSD from the file and show a small "me vs typical TAG" table plus a play-style label (TAG/LAG/nit/station). Caveat LOUDLY first: this is one small session, directional only, and you may miscount on a by-hand count — never hard-diagnose a leak off a tiny sample; point to the specific hands instead.

This is GTO-principle analysis, not a solver run. Never invent cards, sizes, or results that aren't in the text; if something's missing, say the read is uncertain.

Attach your hand-history .txt and say "review my hands."
```

- [ ] **Step 2: Check the prompt body length (URL-fit budget)**

Run (extracts everything after the `---` marker and counts characters):

```bash
cd ~/Developer/poker-tools
awk 'f{print} /^---$/{f=1}' lite/coach-prompt.md | sed '1{/^$/d}' | wc -c
```

Expected: a number. Target ≤ **1800**. If it exceeds 1800, trim by removing the
parenthetical examples first — delete `("this is a clear mistake," "this is spew")`
and `(TAG/LAG/nit/station)` — then re-run until ≤1800. Record the final count.

- [ ] **Step 3: Verify fidelity against SKILL.md**

Run:

```bash
cd ~/Developer/poker-tools
for kw in "blunt" "cooler" "ICM" "stack" "VPIP" "PFR" "3-Bet" "C-Bet" "WTSD" "pot odds" "solver" "invent"; do
  printf '%-10s ' "$kw"; grep -qi "$kw" lite/coach-prompt.md && echo "present" || echo "MISSING"
done
```

Expected: every keyword prints `present`. If any prints `MISSING`, add the
missing concept back into the prompt body (keeping under the 1800 budget).

- [ ] **Step 4: Commit**

```bash
cd ~/Developer/poker-tools
git add lite/coach-prompt.md
git commit -m "feat(lite): add canonical no-install coaching prompt"
```

---

## Task 2: Bring the landing page into the repo

**Files:**
- Create: `docs/index.html` (copied from the session-outputs standalone page)

- [ ] **Step 1: Copy the existing page into the repo**

The standalone page already built (with the sample-card PNG embedded) lives in
the session outputs. Copy it verbatim:

```bash
cd ~/Developer/poker-tools
SRC="/Users/gyndok/Library/Application Support/Claude/local-agent-mode-sessions/a57ee765-2f76-4df8-9f01-0a5b401d09ce/fec6c387-a2be-40a1-9e2b-6783795c7b5d/local_c688ec06-ef40-4640-8340-737a549c8b58/outputs/poker-start-here.html"
mkdir -p docs
cp "$SRC" docs/index.html
ls -la docs/index.html
```

Expected: `docs/index.html` exists, ~233 KB.

- [ ] **Step 2: Verify it's intact and self-contained**

```bash
cd ~/Developer/poker-tools
grep -c 'data:image/png;base64' docs/index.html   # expect: 1 (PNG still embedded)
grep -oE 'href="https://[^"]*"' docs/index.html | sort -u   # expect only the github.com/gyndok/poker-tools link
```

Expected: PNG count = 1; the only external href is the GitHub repo link.

- [ ] **Step 3: Commit**

```bash
cd ~/Developer/poker-tools
git add docs/index.html
git commit -m "docs: add landing page to repo for GitHub Pages"
```

---

## Task 3: Add the "Try it free — no install" section to the page

**Files:**
- Modify: `docs/index.html`

- [ ] **Step 1: Find the insertion point**

```bash
cd ~/Developer/poker-tools
grep -n 'What it does\|What you need\|How to install\|<body' docs/index.html | head
```

Note the line of the first major content heading after the hero (expected to be
`<h2>What it does</h2>` or `<h2>What you need</h2>`). The new `<section>` will be
inserted immediately BEFORE that heading's opening tag so the free path sits at
the top, above the plugin instructions.

- [ ] **Step 2: Insert the lite section**

Insert this exact block immediately before the heading identified in Step 1
(use an Edit with the heading line as the anchor, e.g. replace
`<h2>What it does</h2>` with the block below followed by `<h2>What it does</h2>`).
The `POKER_COACH_PROMPT` template literal MUST be the verbatim prompt body from
`lite/coach-prompt.md` (everything after its `---` marker). The prompt contains
no backticks, backslashes, or `${`, so it is safe inside a JS template literal.

```html
<!-- LITE PATH: try it free, no install -->
<section id="try-free" style="max-width:680px;margin:2rem auto;padding:1.5rem;border:1px solid #2a2a2a;border-radius:12px;background:#141414;">
  <h2 style="margin-top:0;">Try it free — no install (about 30 seconds)</h2>
  <p>Have a free Claude account? Get a hand-by-hand review right now in your browser — <strong>no app, no plugin, no GitHub</strong>. Best with one tournament file at a time.</p>
  <p>
    <a id="open-in-claude" href="#" target="_blank" rel="noopener"
       style="display:inline-block;padding:.7rem 1.2rem;background:#d97757;color:#fff;border-radius:8px;text-decoration:none;font-weight:600;">Open in Claude →</a>
    <button id="copy-prompt" type="button"
       style="padding:.7rem 1.2rem;margin-left:.5rem;background:#2a2a2a;color:#eee;border:1px solid #3a3a3a;border-radius:8px;font-weight:600;cursor:pointer;">📋 Copy the coaching prompt</button>
    <span id="copy-status" style="margin-left:.5rem;color:#7fd17f;font-weight:600;"></span>
  </p>
  <details style="margin-top:1rem;">
    <summary style="cursor:pointer;">How to get your hand-history file</summary>
    <p style="margin:.5rem 0 0;">In the America's Cardroom client, turn on hand-history saving (Settings → enable "Save hand histories"). Your files are named <code>HH….txt</code> and live in your ACR <code>handHistory/&lt;screen name&gt;</code> folder. After clicking the button or pasting the prompt, attach one tournament file to the chat.</p>
  </details>
  <p style="font-size:.9rem;color:#999;margin-top:1rem;">Want your <em>whole archive</em> with exact tracker stats? Use the plugin (Cowork or Claude Code) — see install below.</p>
</section>
<script>
  // Coaching prompt — keep in sync with lite/coach-prompt.md
  const POKER_COACH_PROMPT = `You are a blunt, no-sugarcoating GTO poker coach. I'll attach an America's Cardroom / Winning Poker Network tournament hand-history .txt. The hero (me) is the player named in the "Dealt to <name>" lines — if that's unclear, ask my screen name before analyzing.

Tone: name leaks as mistakes, plainly ("this is a clear mistake," "this is spew"). Don't cushion criticism with compliments. But a cooler is not a leak — separate "got it in ahead, ran bad" (variance, move on) from "this decision loses EV" (a mistake). Praise only genuinely good, non-obvious plays, in one sentence.

Do this:
1) List every hand I did NOT fold preflop, numbered, with level/blinds, my position, my hand, my preflop action, and how far it went. Then review them one at a time; when I say "next," continue in order.
2) For each hand: a setup line (level/blinds+ante, position, exact hand, stack in chips and BB, who covers); a street-by-street action recap with bet sizes as % of pot and the board; then a blunt GTO verdict per decision (preflop range/sizing, c-bet/check, calls vs barrels, river). Show pot odds when a call is close. Adjust for ICM and stack depth — pay jumps/bubble mean tighter than chip-EV, sub-25bb is push/fold, antes widen ranges. End with one bolded takeaway.
3) When I ask for stats, count VPIP, PFR, 3-Bet, C-Bet, and WTSD from the file and show a small "me vs typical TAG" table plus a play-style label (TAG/LAG/nit/station). Caveat LOUDLY first: this is one small session, directional only, and you may miscount on a by-hand count — never hard-diagnose a leak off a tiny sample; point to the specific hands instead.

This is GTO-principle analysis, not a solver run. Never invent cards, sizes, or results that aren't in the text; if something's missing, say the read is uncertain.

Attach your hand-history .txt and say "review my hands."`;
  document.getElementById('open-in-claude').href =
    'https://claude.ai/new?q=' + encodeURIComponent(POKER_COACH_PROMPT);
  document.getElementById('copy-prompt').addEventListener('click', async () => {
    const status = document.getElementById('copy-status');
    try {
      await navigator.clipboard.writeText(POKER_COACH_PROMPT);
      status.textContent = 'Copied!';
    } catch (e) {
      status.textContent = 'Press ⌘/Ctrl-C to copy';
    }
    setTimeout(() => { status.textContent = ''; }, 2500);
  });
</script>
<!-- /LITE PATH -->
```

- [ ] **Step 3: Verify the embedded prompt matches the canonical file**

This guards against drift between `lite/coach-prompt.md` and the HTML string.

```bash
cd ~/Developer/poker-tools
# Canonical body (after the --- marker), normalized
awk 'f{print} /^---$/{f=1}' lite/coach-prompt.md | sed '1{/^$/d}' > /tmp/canon.txt
# Extracted JS template-literal body
awk '/const POKER_COACH_PROMPT = `/{f=1;sub(/.*= `/,"")} f{print} /`;$/{if(f){exit}}' docs/index.html \
  | sed 's/`;$//' > /tmp/embed.txt
diff <(sed -e 's/[[:space:]]*$//' /tmp/canon.txt) <(sed -e 's/[[:space:]]*$//' /tmp/embed.txt) && echo "MATCH"
```

Expected: `MATCH` (no diff output). If they differ, fix the HTML string to match
the `.md` exactly.

- [ ] **Step 4: Verify the section and wiring are present**

```bash
cd ~/Developer/poker-tools
grep -c 'id="try-free"' docs/index.html          # expect 1
grep -c 'id="open-in-claude"' docs/index.html    # expect 1
grep -c 'claude.ai/new?q=' docs/index.html       # expect 1
grep -c 'data:image/png;base64' docs/index.html  # expect 1 (PNG untouched)
```

Expected: first three = 1, PNG still = 1.

- [ ] **Step 5: Open the page and eyeball it**

```bash
open docs/index.html
```

Confirm visually: the "Try it free" section appears above the plugin install
section; the **Open in Claude** button and **Copy** button render; clicking Copy
shows "Copied!". (The button's destination is verified with the user in Task 6.)

- [ ] **Step 6: Commit**

```bash
cd ~/Developer/poker-tools
git add docs/index.html
git commit -m "feat(lite): add no-install 'try it free' path to landing page"
```

---

## Task 4: Merge to main and push

**Files:** none (git only)

GitHub Pages will serve from `main`/`docs`, so the work must land on `main`.

- [ ] **Step 1: Merge the feature branch into main**

```bash
cd ~/Developer/poker-tools
git checkout main
git merge --no-ff feat/lite-path -m "Merge feat/lite-path: no-install lite on-ramp"
```

Expected: fast clean merge (no conflicts — `main` is unchanged since the clone).

- [ ] **Step 2: Push main**

```bash
cd ~/Developer/poker-tools
git push origin main
```

Expected: push succeeds; `main` on GitHub now has `docs/index.html` and
`lite/coach-prompt.md`.

---

## Task 5: Enable GitHub Pages and verify it's live

**Files:** none (GitHub API)

- [ ] **Step 1: Enable Pages from main/docs via API**

```bash
gh api -X POST repos/gyndok/poker-tools/pages \
  -f 'source[branch]=main' -f 'source[path]=/docs' 2>&1 || \
gh api -X PUT repos/gyndok/poker-tools/pages \
  -f 'source[branch]=main' -f 'source[path]=/docs' 2>&1
```

Expected: JSON describing the Pages site (a `409` "already exists" is fine — the
second `PUT` updates it). Record the returned `html_url`.

- [ ] **Step 2: Confirm the Pages config**

```bash
gh api repos/gyndok/poker-tools/pages --jq '{url:.html_url, branch:.source.branch, path:.source.path, status:.status}'
```

Expected: `branch: main`, `path: /docs`, `url: https://gyndok.github.io/poker-tools/`.

- [ ] **Step 3: Wait for the first build, then check it returns 200**

Pages builds take ~1–2 min on first deploy. Poll:

```bash
for i in $(seq 1 20); do
  code=$(curl -s -o /dev/null -w '%{http_code}' https://gyndok.github.io/poker-tools/)
  echo "attempt $i: HTTP $code"; [ "$code" = "200" ] && break; sleep 15
done
```

Expected: eventually `HTTP 200`.

- [ ] **Step 4: Confirm the live page has the lite section**

```bash
curl -s https://gyndok.github.io/poker-tools/ | grep -c 'id="try-free"'
```

Expected: `1`.

---

## Task 6: User-assisted verification of the one-click URL

**Files:** none (manual — requires a logged-in claude.ai session, which can't be
done headlessly).

- [ ] **Step 1: Ask the user to test the button**

Tell the user: open `https://gyndok.github.io/poker-tools/`, click **Open in
Claude**, and confirm a new claude.ai chat opens with the coaching prompt
pre-filled in the composer (not truncated). Then attach a real `HH….txt` and say
"review my hands" to confirm the lite flow works end to end.

- [ ] **Step 2: Handle truncation if reported**

If the pre-filled prompt is cut off, the `q=` length cap was exceeded. The copy
button still delivers the full prompt, so: (a) keep the button but change its
sub-text to "or use Copy below for the full version," OR (b) trim
`lite/coach-prompt.md` and re-sync per Task 3 Step 3, then re-run Tasks 4–5.
Record which path was taken.

---

## Self-Review

**Spec coverage:**
- Lite prompt (canonical, ≤1800, faithful to SKILL.md) → Task 1. ✓
- Delivery = both (button + copy, same text) → Task 3 (single `POKER_COACH_PROMPT`, drift check Step 3). ✓
- Scope = both (review + caveated stats) → Task 1 prompt items 1–3. ✓
- "How to get your file" note → Task 3 `<details>` block. ✓
- Two-path fork (free primary, plugin demoted) → Task 3 section placed above install + "whole archive" pointer. ✓
- Publish to Pages from /docs → Tasks 4–5. ✓
- Page stays self-contained (PNG embedded) → Task 2 Step 2, Task 3 Step 4 checks. ✓
- URL-length risk + graceful degradation → Task 6. ✓
- Tweet reword: spec marks it out-of-repo; not a code task — surfaced to user at the end, no task needed.

**Placeholder scan:** No TBD/TODO; all code, prompt text, and commands are literal.

**Type/name consistency:** `POKER_COACH_PROMPT`, element ids (`try-free`,
`open-in-claude`, `copy-prompt`, `copy-status`), and file paths
(`lite/coach-prompt.md`, `docs/index.html`) are used identically across Tasks 1, 3, 5.
