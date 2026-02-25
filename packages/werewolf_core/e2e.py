#!/usr/bin/env python3
"""End-to-end deterministic simulation harness for judge/player/core.

This module wires:
- JudgeOrchestrator (FSM + protocol + channels)
- GameCore (state resolution)
- werewolf-player responder (structured replies)
"""

from __future__ import annotations

import json
import random
import subprocess
import sys
from pathlib import Path
from typing import Any

from .fsm import GamePhase
from .game import GameCore, Role
from .orchestrator import JudgeOrchestrator
from .protocol import ValidationError


def _default_target(candidates: list[str], avoid: str | None = None) -> str | None:
    for c in candidates:
        if avoid is None or c != avoid:
            return c
    return candidates[0] if candidates else None


def _invoke_player_responder(task: dict[str, Any], responder_path: Path) -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, str(responder_path)],
        input=json.dumps(task, ensure_ascii=False),
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"responder failed: {proc.stderr.strip()}")
    return json.loads(proc.stdout)


def _build_task(
    *,
    game_id: str,
    phase: str,
    player_id: str,
    alive_players: list[str],
    day: int,
    public_feed: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "game_id": game_id,
        "phase": phase,
        "player_id": player_id,
        "schema_version": "v1",
        "visible_context": {
            "day": day,
            "public": public_feed,
            "alive_players": alive_players,
        },
        "action_options": [p for p in alive_players if p != player_id],
        "deadline_s": 30,
    }


def simulate_game_6p(
    *,
    seed: int = 7,
    max_days: int = 6,
    state_file: str | None = None,
) -> dict[str, Any]:
    """Run a 6-player deterministic simulation and return summary."""
    random.seed(seed)

    players = [f"p{i}" for i in range(1, 7)]
    core = GameCore(state_file=state_file)
    setup = core.setup_game(players, "6人")

    wolves = [a["player"] for a in setup["assignments"] if a["role"] == Role.WEREWOLF.value]
    seers = [a["player"] for a in setup["assignments"] if a["role"] == Role.SEER.value]
    witches = [a["player"] for a in setup["assignments"] if a["role"] == Role.WITCH.value]

    game_id = f"sim-6p-seed-{seed}"
    repo_root = Path(__file__).resolve().parents[2]
    responder_path = repo_root / "skills" / "werewolf-player" / "responder.py"

    orchestrator = JudgeOrchestrator(players=players, wolves=wolves)
    public_feed: list[dict[str, Any]] = []

    orchestrator.transition(GamePhase.NIGHT_WEREWOLF)

    winner: str | None = None
    days_played = 0

    while core.state.day <= max_days:
        days_played = core.state.day
        alive = [p.name for p in core.state.players if p.alive]

        # Night werewolf
        alive_wolves = [p for p in wolves if p in alive]
        werewolf_target: str | None = None
        for wolf in alive_wolves:
            task = _build_task(
                game_id=game_id,
                phase="night_werewolf",
                player_id=wolf,
                alive_players=alive,
                day=core.state.day,
                public_feed=public_feed,
            )
            orchestrator.validate_judge_task_payload(task)
            try:
                reply = _invoke_player_responder(task, responder_path)
                reply = orchestrator.accept_player_reply(reply, actor=wolf)
            except (ValidationError, RuntimeError):
                reply = {
                    "intent": "night_action",
                    "content": {
                        "target": _default_target([p for p in alive if p not in alive_wolves]),
                        "speech": "degraded",
                        "confidence": 0.0,
                    },
                }
            target = reply.get("content", {}).get("target")
            if target in alive and target not in alive_wolves:
                werewolf_target = target
            orchestrator.channel_write(
                "wolf_private",
                actor=wolf,
                payload={"day": core.state.day, "target": target, "intent": "night_action"},
            )

        if werewolf_target is None:
            werewolf_target = _default_target([p for p in alive if p not in alive_wolves])

        orchestrator.transition(GamePhase.NIGHT_SEER)

        seer_check: str | None = None
        if seers:
            seer = seers[0]
            if seer in alive:
                task = _build_task(
                    game_id=game_id,
                    phase="night_seer",
                    player_id=seer,
                    alive_players=alive,
                    day=core.state.day,
                    public_feed=public_feed,
                )
                orchestrator.validate_judge_task_payload(task)
                try:
                    reply = _invoke_player_responder(task, responder_path)
                    reply = orchestrator.accept_player_reply(reply, actor=seer)
                    target = reply.get("content", {}).get("target")
                    if target in alive and target != seer:
                        seer_check = target
                except (ValidationError, RuntimeError):
                    seer_check = _default_target([p for p in alive if p != seer])

        orchestrator.transition(GamePhase.NIGHT_WITCH)

        witch_save = False
        witch_poison_target: str | None = None
        if witches:
            witch = witches[0]
            if witch in alive:
                task = _build_task(
                    game_id=game_id,
                    phase="night_witch",
                    player_id=witch,
                    alive_players=alive,
                    day=core.state.day,
                    public_feed=public_feed,
                )
                orchestrator.validate_judge_task_payload(task)
                try:
                    reply = _invoke_player_responder(task, responder_path)
                    reply = orchestrator.accept_player_reply(reply, actor=witch)
                    maybe_target = reply.get("content", {}).get("target")
                    if maybe_target in alive and maybe_target != witch:
                        witch_poison_target = maybe_target
                except (ValidationError, RuntimeError):
                    pass

        night_result = core.process_night(
            {
                "werewolf_target": werewolf_target,
                "seer_check": seer_check,
                "witch_save": witch_save,
                "witch_poison_target": witch_poison_target,
            }
        )

        orchestrator.channel_write(
            "night_actions",
            actor="judge",
            payload={
                "day": core.state.day,
                "werewolf_target": werewolf_target,
                "seer_check": seer_check,
                "witch_save": witch_save,
                "witch_poison_target": witch_poison_target,
            },
        )

        orchestrator.transition(GamePhase.DAY_ANNOUNCE)

        announce = {
            "day": core.state.day,
            "event": "night_result",
            "deaths": night_result["deaths"],
        }
        public_feed.append(announce)
        orchestrator.channel_write("public", actor="judge", payload=announce)

        winner = core.check_winner()
        if winner:
            orchestrator.transition(GamePhase.GAME_OVER)
            break

        orchestrator.transition(GamePhase.DAY_SPEECH)

        alive = [p.name for p in core.state.players if p.alive]
        for player in alive:
            task = _build_task(
                game_id=game_id,
                phase="day_speech",
                player_id=player,
                alive_players=alive,
                day=core.state.day,
                public_feed=public_feed,
            )
            orchestrator.validate_judge_task_payload(task)
            try:
                reply = _invoke_player_responder(task, responder_path)
                reply = orchestrator.accept_player_reply(reply, actor=player)
                speech = reply.get("content", {}).get("speech") or "过"
            except (ValidationError, RuntimeError):
                speech = "过（degraded）"
            payload = {"day": core.state.day, "speaker": player, "speech": speech}
            public_feed.append(payload)
            orchestrator.channel_write("public", actor=player, payload=payload)

        orchestrator.transition(GamePhase.DAY_VOTE)

        alive = [p.name for p in core.state.players if p.alive]
        votes: dict[str, str] = {}
        for voter in alive:
            task = _build_task(
                game_id=game_id,
                phase="day_vote",
                player_id=voter,
                alive_players=alive,
                day=core.state.day,
                public_feed=public_feed,
            )
            orchestrator.validate_judge_task_payload(task)
            try:
                reply = _invoke_player_responder(task, responder_path)
                reply = orchestrator.accept_player_reply(reply, actor=voter)
                target = reply.get("content", {}).get("target")
            except (ValidationError, RuntimeError):
                target = None

            if target not in alive or target == voter:
                target = _default_target([p for p in alive if p != voter])
            if target:
                votes[voter] = target

        vote_result = core.process_vote(votes)
        public_feed.append(
            {
                "day": core.state.day,
                "event": "vote_result",
                "out": vote_result["out"],
                "counts": vote_result["counts"],
            }
        )

        winner = core.check_winner()
        if winner:
            orchestrator.transition(GamePhase.GAME_OVER)
            break

        orchestrator.transition(GamePhase.DAY_LAST_WORDS)
        orchestrator.transition(GamePhase.NIGHT_WEREWOLF)
        core.state.day += 1

    if not winner:
        winner = core.check_winner() or "超时平局"
        if orchestrator.fsm.phase != GamePhase.GAME_OVER:
            orchestrator.transition(GamePhase.GAME_OVER)

    return {
        "game_id": game_id,
        "seed": seed,
        "winner": winner,
        "days_played": days_played,
        "phase": orchestrator.fsm.phase.value,
        "public_messages": len(public_feed),
        "audit_events": len(orchestrator.audit_log),
    }
