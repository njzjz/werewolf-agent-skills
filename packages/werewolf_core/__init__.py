"""werewolf_core: deterministic orchestration primitives for werewolf-agent-skills.

This package intentionally keeps logic machine-readable and testable:
- protocol schemas + validators
- finite state machine (FSM)
- communication channels and ACL
- prompt compiler from templates
- deterministic game resolution core
- formal deterministic game runner (no LLM dependency)
- batch regression simulation helpers
"""

from .batch import run_batch_simulations
from .fsm import FSMError, GamePhase, WerewolfFSM
from .game import GameCore, Role, Team
from .orchestrator import JudgeOrchestrator
from .protocol import ValidationError, validate_judge_task, validate_player_reply
from .runner import simulate_game_6p

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
