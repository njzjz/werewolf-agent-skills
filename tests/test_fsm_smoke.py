#!/usr/bin/env python3
"""Smoke test for FSM transitions and summary output."""

from packages.werewolf_core.fsm import GamePhase
from packages.werewolf_core.orchestrator import JudgeOrchestrator


def test_fsm_flow_and_summary() -> None:
    o = JudgeOrchestrator(players=["p1", "p2"], wolves=["p1"])

    assert o.phase_summary()["phase"] == "setup"

    o.transition(GamePhase.NIGHT_WEREWOLF)
    o.transition(GamePhase.NIGHT_SEER)
    o.transition(GamePhase.NIGHT_WITCH)
    o.transition(GamePhase.DAY_ANNOUNCE)

    summary = o.phase_summary()
    assert summary["phase"] == "day_announce"
    assert "day_speech" in summary["allowed_actions"]
    assert summary["next_step"] == "day_speech"


def test_fsm_next_step_preserves_canonical_order() -> None:
    o = JudgeOrchestrator(players=["p1", "p2"], wolves=["p1"])
    o.transition(GamePhase.NIGHT_WEREWOLF)
    o.transition(GamePhase.NIGHT_SEER)
    o.transition(GamePhase.NIGHT_WITCH)
    o.transition(GamePhase.DAY_ANNOUNCE)
    o.transition(GamePhase.DAY_SPEECH)
    o.transition(GamePhase.DAY_VOTE)
    o.transition(GamePhase.DAY_LAST_WORDS)

    summary = o.phase_summary()
    assert summary["allowed_actions"] == ["night_werewolf", "game_over"]
    assert summary["next_step"] == "night_werewolf"
