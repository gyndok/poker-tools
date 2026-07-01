"""Tests for spot.py — computes the pot geometry the solver spot-sheet needs.

Hand #6 in the review list (fixture hand 1009): hero opens BTN to 250, BB calls,
flop [Kd 7s 2h] with Main pot 550, hero bets 275 (a clean 50% c-bet), BB calls,
turn/river check through, hero wins at showdown. 100 bb effective, ~17.7 SPR.
"""
from conftest import FIXTURE_DIR
import spot

# A short BB whose posted blind is part of its committed chips: the effective
# stack must count the blind. shorty starts 300, commits 100 (blind) + 150 (call)
# = 250, leaving 50 behind = 0.5 bb. Guards the bug where blinds (posted in the
# pre-HOLE-CARDS segment) were dropped, which read the stack as 1.5 bb behind.
_SHORT_BB_HAND = """\
Game Hand #2001 - Tournament #900000002 - Holdem(No Limit) - Level 3 (50.00/100.00)- 2026/06/25 18:00:00 UTC
Table '1' 3-max Seat #1 is the button
Seat 1: hero (10000.00)
Seat 2: sbvill (10000.00)
Seat 3: shorty (300.00)
sbvill posts the small blind 50.00
shorty posts the big blind 100.00
*** HOLE CARDS ***
Dealt to hero [Ah Ac]
hero raises 250.00 to 250.00
sbvill folds
shorty calls 150.00
*** FLOP *** [Ks 7d 2c]
Main pot 550.00
shorty checks
hero bets 275.00
shorty folds
Uncalled bet (275.00) returned to hero
hero did not show and won 550.00
*** SUMMARY ***
Total pot 550.00
"""


def _flop():
    return spot.analyze_hand(FIXTURE_DIR, "hero", 6, "flop")


def test_effective_behind_includes_posted_blind():
    g = spot.analyze_text(_SHORT_BB_HAND, "hero", "flop")
    assert g["eff_bb"] == 3.0            # shorty starts with 300 = 3 bb
    assert g["eff_behind_bb"] == 0.5     # 300 - 100 blind - 150 call = 250 in, 50 behind
    assert g["spr"] == 0.1               # 50 behind / 550 pot
    assert g["bets"][0]["pct"] == 50     # hero bets 275 into 550


def test_blinds_and_effective_stack():
    g = _flop()
    assert g["sb"] == 50.0
    assert g["bb"] == 100.0
    assert g["eff_bb"] == 100.0


def test_pot_at_start_of_flop():
    g = _flop()
    assert g["pot_start"] == 550.0
    assert g["pot_start_bb"] == 5.5


def test_spr_at_flop():
    g = _flop()
    assert g["spr"] == 17.7


def test_cbet_size_as_pct_of_pot():
    g = _flop()
    bets = g["bets"]
    assert len(bets) == 1
    assert bets[0]["player"] == "hero"
    assert bets[0]["amount"] == 275.0
    assert bets[0]["pct"] == 50
