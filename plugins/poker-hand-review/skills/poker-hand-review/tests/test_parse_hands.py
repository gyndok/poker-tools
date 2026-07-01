"""Tests for parse_hands.py against a synthetic 6-max ACR fixture.

The fixture (tests/fixtures/HH20260625 …) contains 9 hands; only 6 are
non-folded-preflop and non-blind-off, so the review list is 1..6:

    #  hole    pos  label        reached
    1  As Kd   CO   open         preflop   (hero open-raises, folds around)
    2  Qh Qs   BTN  3bet         preflop   (villain opens, hero 3-bets)
    3  9h 9c   BTN  call         flop      (hero flats a CO open, folds to c-bet)
    4  Ad Qc   HJ   open         flop      (hero opens + c-bets)
    5  7s 2h   BB   check(BB)    flop      (limped pot, hero checks option)
    6  Ah Kh   BTN  open         showdown  (hero opens, wins at showdown)
"""
import os

from conftest import FIXTURE_DIR
import parse_hands


def _rows():
    files, _ = parse_hands.find_files(FIXTURE_DIR)
    return parse_hands.hand_rows(files, "hero")


def test_review_list_has_six_hands():
    rows = _rows()
    assert [r["n"] for r in rows] == [1, 2, 3, 4, 5, 6]
    assert [r["hole"] for r in rows] == [
        "As Kd", "Qh Qs", "9h 9c", "Ad Qc", "7s 2h", "Ah Kh"
    ]


def test_open_is_labelled_open_not_3bet():
    # regression for the bug where every raise was hard-coded to "raise/3bet"
    rows = _rows()
    assert rows[0]["action"] == "open"   # hero opens the CO
    assert rows[3]["action"] == "open"   # hero opens the HJ + c-bets


def test_three_bet_is_labelled_3bet():
    rows = _rows()
    assert rows[1]["action"] == "3bet"   # hero 3-bets over a villain open


def test_flat_call_and_bb_check_labels():
    rows = _rows()
    assert rows[2]["action"] == "call"        # hero flats an open
    assert rows[4]["action"] == "check(BB)"   # hero checks the BB option


def test_positions_6max():
    rows = _rows()
    pos = {r["n"]: r["pos"] for r in rows}
    assert pos == {1: "CO", 2: "BTN", 3: "BTN", 4: "HJ", 5: "BB", 6: "BTN"}


def test_utg_open_is_labelled_utg_not_mp():
    # hand #1006 (hero opens UTG, folds to a 3-bet) is not in the review list,
    # but its raw text exercises the 6-max early-position label directly.
    files, _ = parse_hands.find_files(FIXTURE_DIR)
    txt = open(files[0], encoding="latin-1").read()
    utg_hand = next(h for h in txt.split("Game Hand #") if "Dealt to hero [Ts Th]" in h)
    assert parse_hands.hero_positions(utg_hand, "hero") == "UTG"
