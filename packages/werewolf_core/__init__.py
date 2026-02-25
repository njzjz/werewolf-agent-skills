"""werewolf_core: deterministic orchestration primitives for werewolf-agent-skills.

This package intentionally keeps logic machine-readable and testable:
- protocol schemas + validators
- finite state machine (FSM)
- communication channels and ACL
- prompt compiler from templates
- deterministic game resolution core
- deterministic e2e simulation harness (no LLM dependency)
- batch regression simulation helpers
"""

from .batch import run_batch_simulations
from .fsm import GamePhase, WerewolfFSM, FSMError
from .game import GameCore, Role, Team
from .e2e import simulate_game_6p
from .protocol import validate_judge_task, validate_player_reply, ValidationError
from .orchestrator import JudgeOrchestrator

__all__ = [
    "GamePhase",
    "WerewolfFSM",
    "FSMError",
    "GameCore",
    "Role",
    "Team",
    "simulate_game_6p",
    "run_batch_simulations",
    "validate_judge_task",
    "validate_player_reply",
    "ValidationError",
    "JudgeOrchestrator",
]
