#!/usr/bin/env python3
"""
Parse America's Cardroom (ACR / WPN) hand histories for one-by-one GTO review.

Usage:
  parse_hands.py --dir <folder> [--hero <screen_name>] [--date YYYYMMDD] list
        List every non-folded-preflop hand in the session (default: latest date),
        numbered continuously across all files, with position/action/how-far.

  parse_hands.py --dir <folder> [--hero ...] [--date ...] dump <N>
        Print the full raw text of hand number N from the list.

The "session" defaults to the most recent YYYYMMDD found in the filenames.
"""
import argparse, glob, os, re, sys

STREETS = ["HOLE CARDS", "FLOP", "TURN", "RIVER", "SHOW DOWN", "SUMMARY"]


def find_files(folder, date=None):
    files = [f for f in glob.glob(os.path.join(folder, "HH*.txt"))]
    if not files:
        # maybe hero subfolder
        sub = glob.glob(os.path.join(folder, "*", "HH*.txt"))
        files = sub or files
    dates = {}
    for f in files:
        m = re.search(r"HH(\d{8})", os.path.basename(f))
        if m:
            dates.setdefault(m.group(1), []).append(f)
    if not dates:
        return [], None
    use = date or max(dates)
    return sorted(dates.get(use, [])), use


def split_streets(hand):
    d = {"PRE": re.split(r"\*\*\* HOLE CARDS \*\*\*", hand)[0]}
    parts = re.split(r"\*\*\* (HOLE CARDS|FLOP|TURN|RIVER|SHOW DOWN|SUMMARY) \*\*\*", hand)
    for i in range(1, len(parts) - 1, 2):
        d[parts[i]] = parts[i + 1]
    return d


# seat labels counting back from the button (offset 0 = BTN)
_POS_FROM_BUTTON = ["BTN", "CO", "HJ", "LJ", "MP", "UTG+1", "UTG+2", "UTG+3"]


def hero_positions(hand, hero):
    """Best-effort position label from button seat + seat order.

    Blinds are read directly from the posts (the reliable signal). The other
    seats are named by their offset from the button, and the first seat to act
    (the earliest non-blind seat) is always UTG — so a 6-max UTG isn't mislabeled
    as MP, which happened when the labels assumed a full 9-handed ring."""
    if re.search(rf"{re.escape(hero)} posts the small blind", hand):
        return "SB"
    if re.search(rf"{re.escape(hero)} posts the big blind", hand):
        return "BB"
    seats = {int(s): n for s, n in re.findall(r"Seat (\d+): (\S+) \(", hand)}
    btn = re.search(r"Seat #(\d+) is the button", hand)
    if not btn or not seats:
        return "?"
    btn = int(btn.group(1))
    order = sorted(seats)
    # rotate so the button is last: rot[0]=SB, rot[1]=BB, …, rot[-1]=BTN
    rot = [s for s in order if s > btn] + [s for s in order if s <= btn]
    hero_seat = next((s for s, n in seats.items() if n == hero), None)
    if hero_seat is None:
        return "?"
    idx = rot.index(hero_seat)
    n = len(rot)
    # the earliest non-blind seat (first to act preflop, rot[2]) is UTG — but only
    # when it isn't itself the button (3-handed, where rot[2] is the BTN).
    if idx == 2 and idx != n - 1:
        return "UTG"
    offset = (n - 1) - idx
    return _POS_FROM_BUTTON[offset] if offset < len(_POS_FROM_BUTTON) else "UTG"


def hand_rows(files, hero):
    rows = []
    idx = 0
    for f in files:
        txt = open(f, encoding="latin-1", errors="replace").read()
        tn = re.search(r"TN-(.*?) GAMETYPE", os.path.basename(f))
        tn = tn.group(1) if tn else os.path.basename(f)
        for h in re.split(r"(?=Game Hand #)", txt):
            if hero not in h:
                continue
            # skip forced blind-off / away hands (site marks the hero "is sitting out")
            if re.search(rf"Seat \d+: {re.escape(hero)} \([\d.]+\) is sitting out", h):
                continue
            d = split_streets(h)
            pre = d.get("HOLE CARDS", "")
            acts = [l.split(hero + " ", 1)[1] for l in pre.splitlines() if l.startswith(hero + " ")]
            if any(a.startswith("folds") for a in acts):
                continue
            if not (any(a.startswith(("raises", "bets", "calls", "checks")) for a in acts)):
                continue
            hole = re.search(rf"Dealt to {re.escape(hero)} \[(.*?)\]", h)
            hole = hole.group(1) if hole else "?"
            lvl = re.search(r"Level (\d+)", h)
            if any(a.startswith("raises") for a in acts):
                # open vs 3-bet: did anyone raise before hero's first raise?
                raises_before = 0
                for l in pre.splitlines():
                    m = re.match(r"(\S.*?) (folds|checks|calls|bets|raises)", l)
                    if not m or "posts" in l:
                        continue
                    if m.group(1) == hero and m.group(2) == "raises":
                        break
                    if m.group(2) == "raises":
                        raises_before += 1
                label = "3bet" if raises_before else "open"
            elif any(a.startswith("calls") for a in acts):
                label = "call"
            elif any(a.startswith("checks") for a in acts):
                label = "check(BB)"
            else:
                label = "?"
            reached = ("showdown" if "SHOW DOWN" in d else "river" if "RIVER" in d
                       else "turn" if "TURN" in d else "flop" if "FLOP" in d else "preflop")
            won = sum(float(x) for x in re.findall(rf"{re.escape(hero)} (?:collected|won) ([\d.]+)", h))
            idx += 1
            rows.append(dict(n=idx, tn=tn, lvl=lvl.group(1) if lvl else "?", hole=hole,
                             pos=hero_positions(h, hero), action=label, reached=reached,
                             won=won, text=h))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--hero", default=None)
    ap.add_argument("--date", default=None)
    ap.add_argument("cmd", choices=["list", "dump"])
    ap.add_argument("num", nargs="?", type=int)
    a = ap.parse_args()

    hero = a.hero or os.path.basename(os.path.normpath(a.dir))
    files, used = find_files(a.dir, a.date)
    if not files:
        print("No hand-history files found in", a.dir); sys.exit(1)
    rows = hand_rows(files, hero)

    if a.cmd == "dump":
        if not a.num or a.num < 1 or a.num > len(rows):
            print("Pick a hand number 1..%d" % len(rows)); sys.exit(1)
        print(rows[a.num - 1]["text"].strip()); return

    print(f"Session {used}  ({len(files)} file(s), hero={hero})")
    cur = None
    print(f"{'#':>2}  {'Lvl':>3}  {'Pos':4} {'Hand':7} {'PF':11} {'Reached':9} {'Won':>9}")
    for r in rows:
        if r["tn"] != cur:
            cur = r["tn"]; print(f"\n— {cur} —")
        print(f"{r['n']:>2}  {r['lvl']:>3}  {r['pos']:4} {r['hole']:7} {r['action']:11} "
              f"{r['reached']:9} {r['won']:>9.0f}")
    print(f"\nTotal non-folded-preflop hands: {len(rows)}")


if __name__ == "__main__":
    main()
