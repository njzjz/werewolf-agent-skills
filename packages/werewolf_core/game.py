#!/usr/bin/env python3
"""Deterministic werewolf game core (state + resolution).

This module is migrated from legacy `skills/werewolf/scripts/game_engine.py`
into reusable core package for judge orchestration.
"""

from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class Role(str, Enum):
    WEREWOLF = "狼人"
    VILLAGER = "平民"
    SEER = "预言家"
    WITCH = "女巫"
    HUNTER = "猎人"
    GUARD = "守卫"
    IDIOT = "白痴"


class Team(str, Enum):
    WEREWOLF = "狼人阵营"
    VILLAGER = "好人阵营"


ROLE_TEAMS = {
    Role.WEREWOLF: Team.WEREWOLF,
    Role.VILLAGER: Team.VILLAGER,
    Role.SEER: Team.VILLAGER,
    Role.WITCH: Team.VILLAGER,
    Role.HUNTER: Team.VILLAGER,
    Role.GUARD: Team.VILLAGER,
    Role.IDIOT: Team.VILLAGER,
}


BOARDS: dict[str, list[Role]] = {
    "6人": [
        Role.WEREWOLF,
        Role.WEREWOLF,
        Role.SEER,
        Role.HUNTER,
        Role.VILLAGER,
        Role.VILLAGER,
    ],
    "9人标准": [
        Role.WEREWOLF,
        Role.WEREWOLF,
        Role.WEREWOLF,
        Role.SEER,
        Role.WITCH,
        Role.HUNTER,
        Role.VILLAGER,
        Role.VILLAGER,
        Role.VILLAGER,
    ],
    "12人标准": [
        Role.WEREWOLF,
        Role.WEREWOLF,
        Role.WEREWOLF,
        Role.WEREWOLF,
        Role.SEER,
        Role.WITCH,
        Role.HUNTER,
        Role.IDIOT,
        Role.VILLAGER,
        Role.VILLAGER,
        Role.VILLAGER,
        Role.VILLAGER,
    ],
}


@dataclass
class Player:
    id: str
    name: str
    role: str | None = None
    team: str | None = None
    alive: bool = True
    can_vote: bool = True
    witch_antidote_used: bool = False
    witch_poison_used: bool = False
    hunter_can_shoot: bool = True
    idiot_revealed: bool = False


@dataclass
class GameState:
    day: int = 0
    players: list[Player] = field(default_factory=list)
    board_name: str = ""
    phase: str = "setup"
    last_night_deaths: list[str] = field(default_factory=list)
    last_day_voted: str | None = None
    winner: str | None = None


class GameCore:
    def __init__(self, state_file: str | None = None):
        self.state_file = Path(state_file) if state_file else None
        self.state = GameState()
        self._load_state()

    def _load_state(self) -> None:
        if self.state_file is None or not self.state_file.exists():
            return
        raw = json.loads(self.state_file.read_text(encoding="utf-8"))
        players = [Player(**p) for p in raw.pop("players", [])]
        self.state = GameState(**raw)
        self.state.players = players

    def _save_state(self) -> None:
        if self.state_file is None:
            return
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(
            json.dumps(asdict(self.state), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _get_player(self, name: str) -> Player | None:
        for p in self.state.players:
            if p.name == name:
                return p
        return None

    def _get_alive_role(self, role: Role) -> Player | None:
        for p in self.state.players:
            if p.alive and p.role == role.value:
                return p
        return None

    def setup_game(self, player_names: list[str], board_name: str = "9人标准") -> dict[str, Any]:
        if board_name not in BOARDS:
            raise ValueError(f"未知板子: {board_name}")

        roles = BOARDS[board_name][:]
        if len(player_names) != len(roles):
            raise ValueError(f"板子 {board_name} 需要 {len(roles)} 人，但给了 {len(player_names)} 人")

        shuffled = [r.value for r in roles]
        random.shuffle(shuffled)

        players: list[Player] = []
        for idx, name in enumerate(player_names):
            role = Role(shuffled[idx])
            players.append(
                Player(
                    id=f"player_{idx + 1}",
                    name=name,
                    role=role.value,
                    team=ROLE_TEAMS[role].value,
                )
            )

        self.state = GameState(
            day=1,
            players=players,
            board_name=board_name,
            phase="night_werewolf",
        )
        self._save_state()

        return {
            "board": board_name,
            "assignments": [
                {"player": p.name, "role": p.role, "team": p.team}
                for p in self.state.players
            ],
        }

    def process_night(self, actions: dict[str, Any]) -> dict[str, Any]:
        """Resolve a full night with collected actions.

        actions example:
          {
            "guard_target": "p2",
            "werewolf_target": "p3",
            "witch_save": true,
            "witch_poison_target": "p5",
            "seer_check": "p1"
          }
        """

        deaths: list[str] = []
        seer_result: dict[str, Any] | None = None

        guarded = actions.get("guard_target")
        werewolf_target = actions.get("werewolf_target")

        if werewolf_target:
            target = self._get_player(werewolf_target)
            if target and target.alive and guarded != werewolf_target:
                deaths.append(werewolf_target)

        witch = self._get_alive_role(Role.WITCH)
        if witch:
            if actions.get("witch_save") and werewolf_target and not witch.witch_antidote_used:
                if guarded == werewolf_target:
                    # 奶穿规则：同守同救 => 仍死亡
                    if werewolf_target not in deaths:
                        deaths.append(werewolf_target)
                else:
                    if werewolf_target in deaths:
                        deaths.remove(werewolf_target)
                witch.witch_antidote_used = True

            poison_target = actions.get("witch_poison_target")
            if poison_target and not witch.witch_poison_used:
                if poison_target not in deaths:
                    deaths.append(poison_target)
                witch.witch_poison_used = True

                poison_player = self._get_player(poison_target)
                if poison_player and poison_player.role == Role.HUNTER.value:
                    poison_player.hunter_can_shoot = False

        seer_target = actions.get("seer_check")
        if seer_target:
            target = self._get_player(seer_target)
            if target:
                seer_result = {
                    "target": seer_target,
                    "is_werewolf": target.role == Role.WEREWOLF.value,
                }

        self.state.last_night_deaths = deaths
        for name in deaths:
            p = self._get_player(name)
            if p:
                p.alive = False

        self.state.phase = "day_announce"
        self._save_state()

        return {
            "deaths": deaths,
            "seer_result": seer_result,
        }

    def process_vote(self, votes: dict[str, str]) -> dict[str, Any]:
        counts: dict[str, int] = {}
        for voter, target in votes.items():
            voter_p = self._get_player(voter)
            target_p = self._get_player(target)
            if not voter_p or not target_p:
                continue
            if not voter_p.alive or not voter_p.can_vote:
                continue
            counts[target] = counts.get(target, 0) + 1

        if not counts:
            return {"out": None, "tie": False, "counts": {}}

        max_votes = max(counts.values())
        candidates = [name for name, c in counts.items() if c == max_votes]

        out_name: str | None = None
        if len(candidates) == 1:
            out_name = candidates[0]
            p = self._get_player(out_name)
            if p:
                p.alive = False
                if p.role == Role.IDIOT.value:
                    p.alive = True
                    p.idiot_revealed = True
                    p.can_vote = False
                    out_name = f"{out_name} (白痴翻牌)"

        self.state.last_day_voted = out_name
        self.state.phase = "day_last_words"
        self._save_state()
        return {"out": out_name, "tie": len(candidates) > 1, "counts": counts}

    def check_winner(self) -> str | None:
        wolves = [p for p in self.state.players if p.alive and p.team == Team.WEREWOLF.value]
        villagers = [p for p in self.state.players if p.alive and p.team == Team.VILLAGER.value]
        gods = [p for p in villagers if p.role != Role.VILLAGER.value]
        peasants = [p for p in villagers if p.role == Role.VILLAGER.value]

        if not wolves:
            self.state.winner = "好人胜利"
            self.state.phase = "game_over"
            self._save_state()
            return self.state.winner

        if not gods or not peasants or len(wolves) >= len(villagers):
            self.state.winner = "狼人胜利"
            self.state.phase = "game_over"
            self._save_state()
            return self.state.winner

        return None

    def public_state(self) -> dict[str, Any]:
        return {
            "day": self.state.day,
            "phase": self.state.phase,
            "board_name": self.state.board_name,
            "alive_players": [p.name for p in self.state.players if p.alive],
            "last_night_deaths": self.state.last_night_deaths,
            "last_day_voted": self.state.last_day_voted,
            "winner": self.state.winner,
        }
