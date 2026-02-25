#!/usr/bin/env python3
"""E2E simulation smoke tests."""

from packages.werewolf_core.e2e import simulate_game_6p


def test_e2e_simulate_game_6p_runs() -> None:
    out = simulate_game_6p(seed=1, max_days=4)
    assert out["winner"]
    assert out["phase"] == "game_over"
    assert out["public_messages"] > 0
    assert out["audit_events"] > 0
