"""werewolf_core: deterministic orchestration primitives for werewolf-agent-skills.

This package intentionally keeps logic machine-readable and testable:
- protocol schemas + validators
- finite state machine (FSM)
- communication channels and ACL
- prompt compiler from templates
"""

from .fsm import GamePhase, WerewolfFSM, FSMError
from .protocol import validate_judge_task, validate_player_reply, ValidationError
from .orchestrator import JudgeOrchestrator

__all__ = [
    "GamePhase",
    "WerewolfFSM",
    "FSMError",
    "validate_judge_task",
    "validate_player_reply",
    "ValidationError",
    "JudgeOrchestrator",
]
