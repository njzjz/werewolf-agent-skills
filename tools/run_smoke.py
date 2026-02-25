#!/usr/bin/env python3
"""Minimal no-dependency smoke runner for werewolf_core.

Usage:
  python3 tools/run_smoke.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from packages.werewolf_core.channels import ChannelAccessError, ChannelRegistry
from packages.werewolf_core.fsm import GamePhase
from packages.werewolf_core.orchestrator import JudgeOrchestrator
from packages.werewolf_core.protocol import ValidationError, validate_judge_task, validate_player_reply


def test_fsm() -> None:
    o = JudgeOrchestrator(players=["p1", "p2"], wolves=["p1"])
    assert o.phase_summary()["phase"] == "setup"
    o.transition(GamePhase.NIGHT_WEREWOLF)
    o.transition(GamePhase.NIGHT_SEER)
    o.transition(GamePhase.NIGHT_WITCH)
    o.transition(GamePhase.DAY_ANNOUNCE)
    assert o.phase_summary()["phase"] == "day_announce"


def test_protocol() -> None:
    task = {
        "game_id": "g1",
        "phase": "day_speech",
        "player_id": "p1",
        "schema_version": "v1",
        "visible_context": {"public": []},
        "action_options": ["p2", "p3"],
        "deadline_s": 30,
    }
    out = validate_judge_task(task)
    assert out["phase"] == "day_speech"

    bad_reply = {
        "game_id": "g1",
        "player_id": "p1",
        "schema_version": "v1",
        "intent": "speak",
        "content": {"speech": "hi", "confidence": 0.5, "hack": True},
    }
    try:
        validate_player_reply(bad_reply)
        raise AssertionError("expected ValidationError")
    except ValidationError as exc:
        assert exc.code == "E_UNKNOWN_FIELD"


def test_channels() -> None:
    channels = ChannelRegistry(wolves=["p1", "p6"], players=["p1", "p2", "p3", "p4", "p5", "p6"])
    wolf_channel = channels.get("wolf_private")
    wolf_channel.write(actor="p1", phase="night_werewolf", payload={"msg": "刀2"})

    try:
        wolf_channel.read(actor="p2", phase="night_werewolf")
        raise AssertionError("non-wolf should not read wolf_private")
    except ChannelAccessError:
        pass


def main() -> None:
    test_fsm()
    test_protocol()
    test_channels()
    print("SMOKE_OK")


if __name__ == "__main__":
    main()
