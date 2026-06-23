# poker-tools — a Claude plugin marketplace

GTO poker tools for [Claude Code](https://code.claude.com) and **Cowork**.
This marketplace currently ships one plugin:

### `poker-hand-review`
Review an America's Cardroom / Winning Poker Network (WPN) session **hand by
hand** with blunt, GTO-based analysis. It:

- finds your most recent session and lists every hand you didn't fold preflop,
- walks through them one at a time with a street-by-street GTO read (preflop
  ranges/sizing, c-bets, calls vs. barrels, rivers), adjusted for **ICM and
  stack depth**, not just raw chip-EV,
- computes session tracker stats — **VPIP, PFR, 3-Bet, Fold-to-3Bet, C-Bet,
  Fold-to-C-Bet, WTSD, W$SD** — and gives a **play-style read** (TAG / LAG / etc.).

The tone is deliberately blunt: it names mistakes as mistakes, but distinguishes
real leaks from coolers and flags small-sample noise.

## Requirements

- **Claude Code or Claude Cowork** (it needs local file access + a Python
  sandbox; plain web chat can't read your hand histories).
- Your ACR/WPN hand-history folder (e.g.
  `…/AmericasCardroom/handHistory/<your_screen_name>/`). The skill infers your
  screen name from the folder name.

## Install

In Claude Code (or via the Cowork plugin menu):

```
/plugin marketplace add gyndok/poker-tools
/plugin install poker-hand-review@poker-tools
```

Then point Claude at your hand-history folder and say **"review my hands"** or
**"run my stats."**

## Notes

- Tuned for No-Limit Hold'em tournaments. Cash (`CASHID-`) and Omaha files are
  detected; Omaha gets a lighter review (different heuristics).
- Stats are directional on small samples — they stabilize over hundreds to
  thousands of hands.
- This is GTO-*principle* analysis, not a live solver run.

## License

MIT
