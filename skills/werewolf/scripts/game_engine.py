#!/usr/bin/env python3
"""
狼人杀游戏引擎 - 管理游戏状态、角色分配、夜间/白天流程
由法官 session 调用
"""

import json
import random
import os
from dataclasses import dataclass, asdict, field
from enum import Enum
from typing import Optional, List, Dict

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

# 预设板子
BOARDS = {
    "6人": [Role.WEREWOLF, Role.WEREWOLF,
            Role.SEER, Role.HUNTER, Role.VILLAGER, Role.VILLAGER],
    "9人标准": [Role.WEREWOLF, Role.WEREWOLF, Role.WEREWOLF,
                Role.SEER, Role.WITCH, Role.HUNTER,
                Role.VILLAGER, Role.VILLAGER, Role.VILLAGER],
    "12人标准": [Role.WEREWOLF, Role.WEREWOLF, Role.WEREWOLF, Role.WEREWOLF,
                 Role.SEER, Role.WITCH, Role.HUNTER, Role.IDIOT,
                 Role.VILLAGER, Role.VILLAGER, Role.VILLAGER, Role.VILLAGER],
}

@dataclass
class Player:
    id: str
    name: str
    role: Optional[str] = None  # Store as string for JSON serialization
    team: Optional[str] = None
    alive: bool = True
    can_vote: bool = True
    witch_antidote_used: bool = False
    witch_poison_used: bool = False
    hunter_can_shoot: bool = True
    idiot_revealed: bool = False
    last_guarded: Optional[str] = None

@dataclass
class GameState:
    day: int = 0
    phase: str = "setup"
    players: List[Player] = field(default_factory=list)
    last_night_deaths: List[str] = field(default_factory=list)
    last_day_voted: Optional[str] = None
    winner: Optional[str] = None

class GameEngine:
    def __init__(self, state_file="game_state.json"):
        self.state_file = state_file
        self.state = GameState()
        self.load_state()

    def save_state(self):
        with open(self.state_file, "w") as f:
            json.dump(asdict(self.state), f, indent=2, ensure_ascii=False)

    def load_state(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    data = json.load(f)
                    players_data = data.pop("players", [])
                    self.state = GameState(**data)
                    self.state.players = [Player(**p) for p in players_data]
            except Exception as e:
                print(f"Error loading state: {e}")

    def setup_game(self, player_names: list[str], board_name: str = "9人标准") -> dict:
        if board_name not in BOARDS:
            return {"error": f"未知板子: {board_name}"}

        board = BOARDS[board_name]
        if len(player_names) != len(board):
            return {"error": f"板子 {board_name} 需要 {len(board)} 人，但提供了 {len(player_names)} 人"}

        roles = [r.value for r in board]
        random.shuffle(roles)

        self.state.players = []
        for i, name in enumerate(player_names):
            role_str = roles[i]
            role_enum = Role(role_str)
            player = Player(
                id=f"player_{i}",
                name=name,
                role=role_str,
                team=ROLE_TEAMS[role_enum].value
            )
            self.state.players.append(player)

        self.state.phase = "night"
        self.state.day = 1
        self.save_state()

        return {
            "success": True,
            "assignments": [
                {"player": p.name, "role": p.role, "team": p.team}
                for p in self.state.players
            ]
        }

    def _get_player(self, name: str) -> Optional[Player]:
        for p in self.state.players:
            if p.name == name:
                return p
        return None

    def _get_witch(self) -> Optional[Player]:
        for p in self.state.players:
            if p.role == Role.WITCH.value and p.alive:
                return p
        return None

    def get_player_role(self, player_name: str) -> Optional[dict]:
        p = self._get_player(player_name)
        if not p:
            return None
        
        teammates = []
        if p.team == Team.WEREWOLF.value:
            teammates = [
                {"name": other.name, "role": other.role}
                for other in self.state.players
                if other.name != p.name and other.team == p.team
            ]
            
        return {
            "name": p.name,
            "role": p.role,
            "team": p.team,
            "teammates": teammates
        }

    def process_night(self, actions: dict) -> dict:
        deaths = []
        results = {"seer_result": None}
        
        # 1. 守卫
        guarded = actions.get("guard_target")
        
        # 2. 狼人
        werewolf_target = actions.get("werewolf_target")
        if werewolf_target:
            target_p = self._get_player(werewolf_target)
            if target_p and target_p.alive:
                if guarded != werewolf_target:
                    deaths.append(werewolf_target)

        # 3. 女巫
        witch = self._get_witch()
        if witch:
            if actions.get("witch_save") and werewolf_target:
                if not witch.witch_antidote_used:
                    if guarded == werewolf_target:
                        # 同守同救 = 死
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
                
                target_p = self._get_player(poison_target)
                if target_p and target_p.role == Role.HUNTER.value:
                    target_p.hunter_can_shoot = False

        # 4. 预言家
        seer_check = actions.get("seer_check")
        if seer_check:
            target_p = self._get_player(seer_check)
            if target_p:
                results["seer_result"] = {
                    "target": seer_check,
                    "is_werewolf": target_p.role == Role.WEREWOLF.value
                }

        # 结算死亡
        self.state.last_night_deaths = deaths
        for d in deaths:
            p = self._get_player(d)
            if p:
                p.alive = False
        
        self.state.phase = "day"
        self.save_state()
        
        return {
            "deaths": deaths,
            "seer_result": results["seer_result"]
        }

    def process_vote(self, votes: dict) -> dict:
        """处理白天投票 votes: {voter_name: target_name}"""
        counts = {}
        for voter, target in votes.items():
            if target not in counts:
                counts[target] = 0
            counts[target] += 1
            
        if not counts:
            return {"out": None, "tie": False}
            
        max_votes = max(counts.values())
        candidates = [p for p, c in counts.items() if c == max_votes]
        
        out_player = None
        if len(candidates) == 1:
            out_player = candidates[0]
            p = self._get_player(out_player)
            if p:
                p.alive = False
                if p.role == Role.IDIOT.value:
                    p.alive = True # 白痴翻牌不死
                    p.idiot_revealed = True
                    p.can_vote = False
                    out_player = f"{out_player} (白痴翻牌)"
        
        self.state.last_day_voted = out_player
        self.save_state()
        return {"out": out_player, "tie": len(candidates) > 1}

    def check_winner(self) -> Optional[str]:
        wolves = [p for p in self.state.players if p.team == Team.WEREWOLF.value and p.alive]
        villagers = [p for p in self.state.players if p.team == Team.VILLAGER.value and p.alive]
        gods = [p for p in villagers if p.role != Role.VILLAGER.value]
        peasants = [p for p in villagers if p.role == Role.VILLAGER.value]
        
        if not wolves:
            return "好人胜利"
        if not gods or not peasants or len(wolves) >= len(villagers):
            return "狼人胜利"
        return None

if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "state"
    engine = GameEngine()
    
    if cmd == "setup":
        players = json.loads(sys.argv[2])
        board = sys.argv[3]
        print(json.dumps(engine.setup_game(players, board), ensure_ascii=False))
    elif cmd == "state":
        print(json.dumps(asdict(engine.state), ensure_ascii=False))
    elif cmd == "night":
        actions = json.loads(sys.argv[2])
        print(json.dumps(engine.process_night(actions), ensure_ascii=False))
    elif cmd == "vote":
        votes = json.loads(sys.argv[2])
        print(json.dumps(engine.process_vote(votes), ensure_ascii=False))
