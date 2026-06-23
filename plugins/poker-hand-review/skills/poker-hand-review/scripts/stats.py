#!/usr/bin/env python3
"""
Compute poker tracker statistics for a session's hand histories (ACR / WPN).

Usage:
  stats.py --dir <folder> [--hero <screen_name>] [--date YYYYMMDD]

Reports VPIP, PFR, 3-Bet, Fold-to-3Bet, Flop C-Bet, Fold-to-C-Bet, WTSD, W$SD,
plus the VPIP-PFR gap and PFR/VPIP ratio used for the style read.

Notes / definitions:
  VPIP  = hero voluntarily calls/bets/raises preflop (posting blinds & BB checks
          do NOT count). Denominator = all hands dealt to hero.
  PFR   = hero raises preflop at least once. Denominator = hands dealt.
  3-Bet = hero re-raises facing exactly one prior open. Denominator = times hero
          faced a single open at first decision (3-bet opportunities).
  F3B   = hero opened, faced a re-raise, and folded. Denom = hero-open-faced-3bet.
  C-Bet = hero is preflop aggressor (last preflop raiser), saw flop, and bet flop
          first. Denom = flops where hero was the aggressor.
  FCB   = hero (not aggressor) faced the aggressor's flop bet and folded.
  WTSD  = hero reached showdown (never folded). Denom = flops hero actually saw.
  W$SD  = hero won at showdown. Denom = showdowns reached.

Hold'em only. Omaha / cash files are skipped for these stats (heuristics differ).
Small samples (a few hundred hands) are NOT statistically reliable; the script
prints the sample size so the reader can caveat appropriately.
"""
import argparse, glob, os, re, sys


def find_files(folder, date=None):
    files = glob.glob(os.path.join(folder, "HH*.txt")) or \
            glob.glob(os.path.join(folder, "*", "HH*.txt"))
    # Hold'em tournaments + Hold'em cash; skip Omaha
    files = [f for f in files if "Omaha" not in os.path.basename(f)]
    dates = {}
    for f in files:
        m = re.search(r"HH(\d{8})", os.path.basename(f))
        if m:
            dates.setdefault(m.group(1), []).append(f)
    if not dates:
        return [], None
    use = date or max(dates)
    return sorted(dates.get(use, [])), use


def pre_seq(hand):
    seg = re.split(r"\*\*\* HOLE CARDS \*\*\*", hand)
    if len(seg) < 2:
        return []
    seg = re.split(r"\*\*\* FLOP|\*\*\* SUMMARY|\*\*\* SHOW", seg[1])[0]
    out = []
    for l in seg.splitlines():
        m = re.match(r"(\S.*?) (folds|checks|calls|bets|raises)", l)
        if m and "posts" not in l:
            out.append((m.group(1), m.group(2)))
    return out


def flop_seq(hand):
    m = re.search(r"\*\*\* FLOP \*\*\*(.*?)(\*\*\* TURN|\*\*\* SHOW|\*\*\* SUMMARY|$)", hand, re.S)
    if not m:
        return None
    out = []
    for l in m.group(1).splitlines():
        mm = re.match(r"(\S.*?) (folds|checks|calls|bets|raises)", l)
        if mm:
            out.append((mm.group(1), mm.group(2)))
    return out


def compute(files, hero):
    H = dict(hands=0, vpip=0, pfr=0, tb_opp=0, tb=0, f3b_opp=0, f3b=0,
             cb_opp=0, cb=0, fcb_opp=0, fcb=0, saw_flop=0, wtsd=0, wsd=0)
    for f in files:
        txt = open(f, encoding="latin-1", errors="replace").read()
        for h in re.split(r"(?=Game Hand #)", txt):
            if f"Dealt to {hero} [" not in h:
                continue
            H['hands'] += 1
            seq = pre_seq(h)
            hero_pre = [a for (p, a) in seq if p == hero]
            folded_pre = "folds" in hero_pre
            if any(a in ("calls", "bets", "raises") for a in hero_pre):
                H['vpip'] += 1
            if "raises" in hero_pre:
                H['pfr'] += 1
            rc = 0; faced_open = False; hero_open = False; hero_3bet = False; acted = False
            for (p, a) in seq:
                if p == hero and not acted:
                    acted = True; faced_open = (rc == 1)
                    if rc == 0 and a == "raises":
                        hero_open = True
                    if rc == 1 and a == "raises":
                        hero_3bet = True
                if a == "raises":
                    rc += 1
            if faced_open:
                H['tb_opp'] += 1
                if hero_3bet:
                    H['tb'] += 1
            if hero_open:
                idxs = [i for i, (p, a) in enumerate(seq) if p == hero]
                openi = next((i for i in idxs if seq[i][1] == "raises"), None)
                if openi is not None:
                    later = seq[openi + 1:]
                    if any(a == "raises" for (p, a) in later if p != hero):
                        H['f3b_opp'] += 1
                        seen3 = False; resp = None
                        for (p, a) in later:
                            if not seen3 and a == "raises" and p != hero:
                                seen3 = True; continue
                            if seen3 and p == hero:
                                resp = a; break
                        if resp == "folds":
                            H['f3b'] += 1
            if folded_pre:
                continue
            fs = flop_seq(h)
            if fs is None:
                continue
            H['saw_flop'] += 1
            last_raiser = None
            for (p, a) in seq:
                if a == "raises":
                    last_raiser = p
            if last_raiser == hero:
                H['cb_opp'] += 1
                first = next((a for (p, a) in fs if p == hero), None)
                if first == "bets":
                    H['cb'] += 1
            else:
                agg_bet = False; resp = None
                for (p, a) in fs:
                    if p == last_raiser and a == "bets":
                        agg_bet = True
                    if agg_bet and p == hero:
                        resp = a; break
                if agg_bet:
                    H['fcb_opp'] += 1
                    if resp == "folds":
                        H['fcb'] += 1
            if "*** SHOW DOWN ***" in h and not re.search(rf"{re.escape(hero)} folds", h):
                H['wtsd'] += 1
                if re.search(rf"{re.escape(hero)} (?:collected|won)", h):
                    H['wsd'] += 1
    return H


def pct(a, b):
    return f"{100*a/b:.0f}%" if b else "n/a"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--hero", default=None)
    ap.add_argument("--date", default=None)
    a = ap.parse_args()
    hero = a.hero or os.path.basename(os.path.normpath(a.dir))
    files, used = find_files(a.dir, a.date)
    if not files:
        print("No Hold'em hand-history files found in", a.dir); sys.exit(1)
    H = compute(files, hero)
    n = H['hands']
    print(f"Session {used} — Hold'em hands dealt to {hero}: {n}")
    if n < 200:
        print("  (small sample — treat stats as directional, not settled)")
    print()
    rows = [
        ("VPIP", pct(H['vpip'], n), f"{H['vpip']}/{n}"),
        ("PFR", pct(H['pfr'], n), f"{H['pfr']}/{n}"),
        ("3-Bet", pct(H['tb'], H['tb_opp']), f"{H['tb']}/{H['tb_opp']} opp"),
        ("Fold to 3-Bet", pct(H['f3b'], H['f3b_opp']), f"{H['f3b']}/{H['f3b_opp']} opp"),
        ("Flop C-Bet", pct(H['cb'], H['cb_opp']), f"{H['cb']}/{H['cb_opp']} opp"),
        ("Fold to C-Bet", pct(H['fcb'], H['fcb_opp']), f"{H['fcb']}/{H['fcb_opp']} opp"),
        ("WTSD", pct(H['wtsd'], H['saw_flop']), f"{H['wtsd']}/{H['saw_flop']} flops"),
        ("W$SD", pct(H['wsd'], H['wtsd']), f"{H['wsd']}/{H['wtsd']}"),
    ]
    for name, p, raw in rows:
        print(f"  {name:<14} {p:>5}  ({raw})")
    if n:
        gap = 100 * (H['vpip'] - H['pfr']) / n
        ratio = (H['pfr'] / H['vpip']) if H['vpip'] else 0
        print(f"\n  VPIP-PFR gap: {gap:.0f} pts   PFR/VPIP ratio: {ratio:.2f}")
    # machine-readable line for the model to build the style read
    print("\nRAW:", H)


if __name__ == "__main__":
    main()
