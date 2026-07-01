#!/usr/bin/env python3
"""
Compute the pot geometry for a single hand's decision node — the numbers a
solver spot-sheet (GTO Wizard / PioSOLVER) needs but that are easy to get wrong
doing mental math over raw chip amounts.

Usage:
  spot.py --dir <folder> [--hero <name>] [--date YYYYMMDD] <N> [--street STREET]
        N       = hand number from `parse_hands.py list` (same review numbering)
        STREET  = flop | turn | river | preflop   (default: flop)

Prints a human-readable spot line plus a machine-readable `RAW: {json}` line.
Everything is derived straight from the hand history: blinds and effective stack
from the header/seat rows, the street-start pot from the site's printed
`Main pot` / `Total pot` line, and each bet as a % of the pot before it went in.
It reports inputs only — never strategy frequencies or EV (that's the solver).

`bets` percentages use the pot *before* the wager: a bet is amount/pot; a raise
is the additional chips over what the player already had in, / pot.
"""
import argparse, json, os, re, sys
from collections import defaultdict

from parse_hands import find_files, hand_rows, split_streets

# betting streets, in order, mapped to their split_streets() segment keys
_STREETS = [("preflop", "HOLE CARDS"), ("flop", "FLOP"),
            ("turn", "TURN"), ("river", "RIVER")]


def _seg_actions(seg):
    """Ordered (player, action, amount) for one street segment. `amount` is the
    chips that action puts in (for a raise it's the raise-*to* total)."""
    out = []
    for l in seg.splitlines():
        m = re.match(r"(\S.*?) posts (?:the )?(?:small blind|big blind|ante|"
                     r"small \& big blinds) ([\d.]+)", l)
        if m:
            out.append((m.group(1), "post", float(m.group(2)))); continue
        m = re.match(r"(\S.*?) raises [\d.]+ to ([\d.]+)", l)
        if m:
            out.append((m.group(1), "raises", float(m.group(2)))); continue
        m = re.match(r"(\S.*?) (bets|calls) ([\d.]+)", l)
        if m:
            out.append((m.group(1), m.group(2), float(m.group(3)))); continue
        m = re.match(r"(\S.*?) (folds|checks)\b", l)
        if m:
            out.append((m.group(1), m.group(2), 0.0)); continue
    return out


def _pot_printed(seg):
    m = re.search(r"(?:Main pot|Total pot) ([\d.]+)", seg)
    return float(m.group(1)) if m else None


def analyze_hand(folder, hero, n, street="flop"):
    files, _ = find_files(folder, None)
    rows = hand_rows(files, hero)
    if n < 1 or n > len(rows):
        raise IndexError(f"hand {n} out of range 1..{len(rows)}")
    return analyze_text(rows[n - 1]["text"], hero, street, n=n)


def analyze_text(text, hero, street="flop", n=None):
    street = street.lower()
    d = split_streets(text)

    m = re.search(r"Level \d+ \(([\d.]+)/([\d.]+)\)", text)
    sb, bb = (float(m.group(1)), float(m.group(2))) if m else (0.0, 0.0)
    stacks = {name: float(s)
              for name, s in re.findall(r"Seat \d+: (\S+) \(([\d.]+)\)", text)}

    # walk the streets that precede the target, tracking each player's total
    # contribution and who has folded, so we know the behind stacks + who's in.
    # Blinds/antes are posted in the pre-HOLE-CARDS segment, so they must be
    # counted too — otherwise a short blind's effective stack reads too deep.
    contributed = defaultdict(float)
    folded = set()
    posts = [(p, amt) for p, a, amt in _seg_actions(d.get("PRE", "")) if a == "post"]
    for p, amt in posts:
        contributed[p] += amt
    for key, seg_key in _STREETS:
        if key == street:
            break
        seg = d.get(seg_key)
        if not seg:
            continue
        street_in = defaultdict(float)
        if seg_key == "HOLE CARDS":
            for p, amt in posts:      # already in `contributed`; seed for raise-delta math
                street_in[p] += amt
        for p, a, amt in _seg_actions(seg):
            if a == "folds":
                folded.add(p)
            elif a == "calls":
                contributed[p] += amt; street_in[p] += amt
            elif a == "bets":
                contributed[p] += amt; street_in[p] = amt
            elif a == "raises":
                contributed[p] += amt - street_in[p]; street_in[p] = amt

    still_in = [p for p in stacks if p not in folded]
    behind = {p: stacks[p] - contributed[p] for p in stacks}
    eff_stack = min((stacks[p] for p in still_in), default=0.0)
    eff_behind = min((behind[p] for p in still_in), default=0.0)

    seg = d.get(dict(_STREETS)[street]) if street in dict(_STREETS) else None
    pot_start = _pot_printed(seg) if seg else None
    if pot_start is None:                       # preflop / missing: fall back to blinds
        pot_start = round(sum(contributed.values()) or (sb + bb), 2)

    # size each aggressive action on this street as a % of the pot before it
    bets = []
    if seg:
        pot = pot_start
        street_in = defaultdict(float)
        for p, a, amt in _seg_actions(seg):
            if a == "bets":
                bets.append({"player": p, "amount": amt,
                             "pct": round(100 * amt / pot) if pot else None})
                pot += amt; street_in[p] = amt
            elif a == "raises":
                added = amt - street_in[p]
                bets.append({"player": p, "amount": amt,
                             "pct": round(100 * added / pot) if pot else None})
                pot += added; street_in[p] = amt
            elif a == "calls":
                pot += amt; street_in[p] += amt

    return {
        "hand_n": n,
        "street": street,
        "sb": sb, "bb": bb,
        "eff_bb": round(eff_stack / bb, 1) if bb else None,
        "eff_behind_bb": round(eff_behind / bb, 1) if bb else None,
        "pot_start": round(pot_start, 2),
        "pot_start_bb": round(pot_start / bb, 1) if bb else None,
        "spr": round(eff_behind / pot_start, 1) if pot_start else None,
        "bets": bets,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--hero", default=None)
    ap.add_argument("--date", default=None)
    ap.add_argument("num", type=int)
    ap.add_argument("--street", default="flop",
                    choices=["preflop", "flop", "turn", "river"])
    a = ap.parse_args()
    hero = a.hero or os.path.basename(os.path.normpath(a.dir))
    files, _ = find_files(a.dir, a.date)
    if not files:
        print("No hand-history files found in", a.dir); sys.exit(1)
    g = analyze_hand(a.dir, hero, a.num, a.street)

    sizes = ", ".join(f"{b['player']} {b['pct']}%" for b in g["bets"]) or "—"
    print(f"SPOT — hand {g['hand_n']}, {g['street']}")
    print(f"  Blinds:     {g['sb']:.0f}/{g['bb']:.0f}")
    print(f"  Effective:  {g['eff_bb']} bb  ({g['eff_behind_bb']} bb behind at this street)")
    print(f"  Pot:        {g['pot_start']:.0f}  ({g['pot_start_bb']} bb)")
    print(f"  SPR:        {g['spr']}")
    print(f"  Bet sizes:  {sizes}")
    print("\nRAW: " + json.dumps(g))


if __name__ == "__main__":
    main()
