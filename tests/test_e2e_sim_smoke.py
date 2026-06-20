#!/usr/bin/env python3
"""Formal game runner smoke tests."""

from werewolf_core.runner import simulate_game_6p


def test_e2e_simulate_game_6p_runs() -> None:
    out = simulate_game_6p(seed=1, max_days=4)
    assert out["winner"]
    assert out["phase"] == "game_over"
    assert out["public_messages"] > 0
    assert out["audit_events"] > 0
