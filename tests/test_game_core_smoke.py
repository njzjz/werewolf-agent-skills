#!/usr/bin/env python3
"""GameCore smoke tests."""

from packages.werewolf_core.game import GameCore


def test_game_core_6p_setup_and_roundtrip(tmp_path) -> None:
    state_file = tmp_path / "game_state.json"
    core = GameCore(state_file=str(state_file))

    players = ["p1", "p2", "p3", "p4", "p5", "p6"]
    setup = core.setup_game(players, "6人")
    assert len(setup["assignments"]) == 6

    # run a minimal night resolve (may or may not kill depending on actions)
    night = core.process_night(
        {
            "werewolf_target": "p3",
            "seer_check": "p1",
        }
    )
    assert "deaths" in night

    # run a day vote
    vote = core.process_vote(
        {
            "p1": "p2",
            "p2": "p3",
            "p3": "p2",
            "p4": "p2",
            "p5": "p2",
            "p6": "p2",
        }
    )
    assert "out" in vote

    # ensure state persisted and can be reloaded
    core2 = GameCore(state_file=str(state_file))
    assert core2.state.board_name == "6人"
