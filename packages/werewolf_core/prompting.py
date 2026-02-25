#!/usr/bin/env python3
"""Prompt compiler with deterministic templates."""

from __future__ import annotations

from pathlib import Path


TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"


def _read_template(name: str) -> str:
    path = TEMPLATE_DIR / name
    return path.read_text(encoding="utf-8")


def build_judge_prompt(game_id: str, board_name: str, players: list[str]) -> str:
    template = _read_template("judge_system_prompt.txt")
    return (
        template.replace("{{game_id}}", game_id)
        .replace("{{board_name}}", board_name)
        .replace("{{players}}", ", ".join(players))
    )


def build_player_prompt(
    game_id: str,
    player_id: str,
    role: str,
    teammates: list[str] | None = None,
) -> str:
    teammates = teammates or []
    template = _read_template("player_system_prompt.txt")
    return (
        template.replace("{{game_id}}", game_id)
        .replace("{{player_id}}", player_id)
        .replace("{{role}}", role)
        .replace("{{teammates}}", ", ".join(teammates) if teammates else "无")
    )
