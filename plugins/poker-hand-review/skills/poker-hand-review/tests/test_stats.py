"""Regression tests locking stats.py counters against the known fixture.

Hand tally (see the fixture header comments in test_parse_hands.py):
  dealt to hero (blind-off excluded) = 8
  VPIP  = 6  (hands 1,2,3,4,6,9)      PFR = 5 (1,2,4,6,9)
  3-Bet = 1 / 2 opp  (opp: 2,3; hit: 2)
  Fold-to-3Bet = 1 / 1 opp  (hand 6)
  Flop C-Bet = 2 / 2 opp  (hands 4,9)
  Fold-to-C-Bet = 1 / 1 opp  (hand 3)
  WTSD = 1 / 4 flops  (hand 9)        W$SD = 1 / 1  (hand 9)
  blind-off excluded = 1  (hand 8, sitting out)
"""
from conftest import FIXTURE_DIR
import stats


def _H():
    files, _ = stats.find_files(FIXTURE_DIR)
    bo = stats.blindoff_ids(files, "hero")
    return stats.compute(files, "hero", skip_ids=bo)


def test_hands_and_blindoff_exclusion():
    H = _H()
    assert H["hands"] == 8
    assert H["blindoff"] == 1


def test_vpip_pfr():
    H = _H()
    assert H["vpip"] == 6
    assert H["pfr"] == 5


def test_three_bet_and_fold_to_three_bet():
    H = _H()
    assert (H["tb"], H["tb_opp"]) == (1, 2)
    assert (H["f3b"], H["f3b_opp"]) == (1, 1)


def test_cbet_and_fold_to_cbet():
    H = _H()
    assert (H["cb"], H["cb_opp"]) == (2, 2)
    assert (H["fcb"], H["fcb_opp"]) == (1, 1)


def test_showdown_stats():
    H = _H()
    assert H["saw_flop"] == 4
    assert (H["wtsd"], H["wsd"]) == (1, 1)
