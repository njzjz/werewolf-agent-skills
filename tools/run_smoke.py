#!/usr/bin/env python3
"""Minimal no-dependency smoke runner for werewolf_core.

Usage:
  python3 tools/run_smoke.py
"""

from __future__ import annotations

import random
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPO_ROOT / "packages"
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from werewolf_core.batch import run_batch_simulations
from werewolf_core.channels import ChannelAccessError, ChannelRegistry
from werewolf_core.fsm import GamePhase
from werewolf_core.game import GameCore
from werewolf_core.orchestrator import JudgeOrchestrator
from werewolf_core.protocol import ValidationError, validate_judge_task, validate_player_reply
from werewolf_core.runner import simulate_game_6p


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


def test_game_core() -> None:
    with tempfile.TemporaryDirectory() as td:
        state_file = Path(td) / "game_state.json"
        core = GameCore(state_file=str(state_file), rng=random.Random(1))
        players = ["p1", "p2", "p3", "p4", "p5", "p6"]
        core.setup_game(players, "6人")

        night = core.process_night({"werewolf_target": "p3", "seer_check": "p1"})
        assert "deaths" in night

        vote = core.process_vote(
            {
                "p1": "p2",
                "p2": "p4",
                "p4": "p2",
                "p5": "p2",
                "p6": "p2",
            }
        )
        assert "out" in vote
        assert vote["rejected"] == []


def test_e2e_sim() -> None:
    out = simulate_game_6p(seed=1, max_days=4)
    assert out["winner"]
    assert out["phase"] == "game_over"


def test_batch() -> None:
    out = run_batch_simulations(runs=3, seed_start=1, max_days=4)
    assert out["summary"]["runs"] == 3


def main() -> None:
    test_fsm()
    test_protocol()
    test_channels()
    test_game_core()
    test_e2e_sim()
    test_batch()
    print("SMOKE_OK")


if __name__ == "__main__":
    main()
