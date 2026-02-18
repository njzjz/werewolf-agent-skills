#!/usr/bin/env python3
"""
狼人杀游戏引擎 - 管理游戏状态、角色分配、夜间/白天流程
由法官 session 调用
"""

import json
import random
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional

class Role(Enum):
    WEREWOLF = "狼人"
    VILLAGER = "平民"
    SEER = "预言家"
    WITCH = "女巫"
    HUNTER = "猎人"
    GUARD = "守卫"
    IDIOT = "白痴"

class Team(Enum):
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

# 预设板子
BOARDS = {
    "6人": [Role.WEREWOLF, Role.WEREWOLF, Role.VILLAGER, Role.VILLAGER, Role.VILLAGER, Role.VILLAGER],
    "9人标准": [Role.WEREWOLF, Role.WEREWOLF, Role.WEREWOLF,
                Role.VILLAGER, Role.VILLAGER, Role.VILLAGER,
                Role.SEER, Role.WITCH, Role.HUNTER],
    "12人完整": [Role.WEREWOLF, Role.WEREWOLF, Role.WEREWOLF, Role.WEREWOLF,
                 Role.VILLAGER, Role.VILLAGER, Role.VILLAGER, Role.VILLAGER,
                 Role.SEER, Role.WITCH, Role.HUNTER, Role.GUARD],
}

@dataclass
class Player:
    id: str
    name: str
    role: Optional[Role] = None
    team: Optional[Team] = None
    alive: bool = True
    can_vote: bool = True
    # 技能状态
    witch_antidote_used: bool = False
    witch_poison_used: bool = False
    hunter_can_shoot: bool = True
    idiot_revealed: bool = False
    last_guarded: Optional[str] = None

@dataclass
class GameState:
    day: int = 0  # 0=游戏未开始, 1=第一天
    phase: str = "setup"  # setup, night, day, ended
    players: list = None
    last_night_deaths: list = None
    last_day_voted: Optional[str] = None
    winner: Optional[str] = None

    def __post_init__(self):
        if self.players is None:
            self.players = []
        if self.last_night_deaths is None:
            self.last_night_deaths = []

class GameEngine:
    def __init__(self):
        self.state = GameState()
        self._night_actions = {}  # 存储夜间行动

    def setup_game(self, player_names: list[str], board_name: str = "9人标准") -> dict:
        """初始化游戏，分配角色"""
        if board_name not in BOARDS:
            available = ", ".join(BOARDS.keys())
            return {"error": f"未知板子: {board_name}. 可用: {available}"}

        board = BOARDS[board_name]
        if len(player_names) != len(board):
            return {"error": f"板子 {board_name} 需要 {len(board)} 人，但提供了 {len(player_names)} 人"}

        # 随机分配角色
        roles = board.copy()
        random.shuffle(roles)

        self.state.players = []
        for i, name in enumerate(player_names):
            role = roles[i]
            player = Player(
                id=f"player_{i}",
                name=name,
                role=role,
                team=ROLE_TEAMS[role]
            )
            self.state.players.append(player)

        self.state.phase = "night"
        self.state.day = 1

        return {
            "success": True,
            "assignments": [
                {"player": p.name, "role": p.role.value, "team": p.team.value}
                for p in self.state.players
            ]
        }

    def get_player_role(self, player_name: str) -> Optional[dict]:
        """获取玩家角色信息（用于告知玩家）"""
        for p in self.state.players:
            if p.name == player_name:
                return {
                    "name": p.name,
                    "role": p.role.value,
                    "team": p.team.value,
                    "teammates": [
                        {"name": other.name, "role": other.role.value}
                        for other in self.state.players
                        if other.name != p.name and other.team == p.team and p.team == Team.WEREWOLF
                    ] if p.team == Team.WEREWOLF else None
                }
        return None

    def get_werewolves(self) -> list[dict]:
        """获取所有狼人（用于狼人互相确认）"""
        return [
            {"name": p.name, "id": p.id}
            for p in self.state.players
            if p.role == Role.WEREWOLF and p.alive
        ]

    def process_night(self, actions: dict) -> dict:
        """
        处理夜间行动
        actions: {
            "werewolf_target": "玩家名",
            "witch_save": true/false,
            "witch_poison_target": "玩家名"/null,
            "seer_check": "玩家名",
            "guard_target": "玩家名"
        }
        """
        deaths = []
        results = {"seer_result": None}

        # 1. 处理守卫
        guarded = actions.get("guard_target")

        # 2. 处理狼人击杀
        werewolf_target = actions.get("werewolf_target")
        if werewolf_target:
            target_player = self._get_player(werewolf_target)
            if target_player and target_player.alive:
                # 检查是否被守护
                if guarded == werewolf_target:
                    # 被守护，不死
                    pass
                else:
                    # 被击杀
                    deaths.append(werewolf_target)

        # 3. 处理女巫
        if actions.get("witch_save") and werewolf_target:
            # 使用解药
            witch = self._get_witch()
            if witch and not witch.witch_antidote_used:
                # 检查奶穿
                if guarded == werewolf_target:
                    # 同守同救，死亡
                    pass  # 已经在deaths中
                else:
                    # 救活
                    if werewolf_target in deaths:
                        deaths.remove(werewolf_target)
                witch.witch_antidote_used = True

        if actions.get("witch_poison_target"):
            poison_target = actions.get("witch_poison_target")
            witch = self._get_witch()
            if witch and not witch.witch_poison_used:
                if poison_target not in deaths:
                    deaths.append(poison_target)
                witch.witch_poison_used = True
                # 被毒死的猎人不能开枪
                target = self._get_player(poison_target)
                if target and target.role == Role.HUNTER:
                    target.hunter_can_shoot = False

        # 4. 处理预言家查验
        seer_check = actions.get("seer_check")
        if seer_check:
            target = self._get_player(seer_check)
            if target:
                results["seer_result"] = {
                    "target": seer_check,
                    "is_werewolf": target.role == Role.WEREWOLF
                }

        # 应用死亡
        for death_name in deaths:
            player = self._get_player(death_name)
            if player:
                player.alive