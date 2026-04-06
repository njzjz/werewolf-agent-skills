#!/usr/bin/env python3
"""Finite State Machine for werewolf orchestration."""

from __future__ import annotations

from enum import Enum


class FSMError(RuntimeError):
    """Raised when an illegal state transition occurs."""


class GamePhase(str, Enum):
    SETUP = "setup"
    NIGHT_WEREWOLF = "night_werewolf"
    NIGHT_SEER = "night_seer"
    NIGHT_WITCH = "night_witch"
    DAY_ANNOUNCE = "day_announce"
    DAY_SPEECH = "day_speech"
    DAY_VOTE = "day_vote"
    DAY_LAST_WORDS = "day_last_words"
    GAME_OVER = "game_over"


ALLOWED_TRANSITIONS: dict[GamePhase, tuple[GamePhase, ...]] = {
    GamePhase.SETUP: (GamePhase.NIGHT_WEREWOLF,),
    GamePhase.NIGHT_WEREWOLF: (GamePhase.NIGHT_SEER,),
    GamePhase.NIGHT_SEER: (GamePhase.NIGHT_WITCH,),
    GamePhase.NIGHT_WITCH: (GamePhase.DAY_ANNOUNCE,),
    GamePhase.DAY_ANNOUNCE: (GamePhase.DAY_SPEECH, GamePhase.GAME_OVER),
    GamePhase.DAY_SPEECH: (GamePhase.DAY_VOTE,),
    GamePhase.DAY_VOTE: (GamePhase.DAY_LAST_WORDS, GamePhase.GAME_OVER),
    GamePhase.DAY_LAST_WORDS: (GamePhase.NIGHT_WEREWOLF, GamePhase.GAME_OVER),
    GamePhase.GAME_OVER: (),
}


class WerewolfFSM:
    """Deterministic phase transition state machine."""

    def __init__(self, phase: GamePhase = GamePhase.SETUP, day: int = 0):
        self.phase = phase
        self.day = day

    def allowed_next(self) -> list[GamePhase]:
        return list(ALLOWED_TRANSITIONS[self.phase])

    def default_next(self) -> GamePhase | None:
        allowed = ALLOWED_TRANSITIONS[self.phase]
        return allowed[0] if allowed else None

    def can_transition(self, to_phase: GamePhase) -> bool:
        return to_phase in ALLOWED_TRANSITIONS[self.phase]

    def transition(self, to_phase: GamePhase) -> None:
        if not self.can_transition(to_phase):
            raise FSMError(
                f"illegal transition: {self.phase.value} -> {to_phase.value}; "
                f"allowed: {[p.value for p in self.allowed_next()]}"
            )

        if self.phase == GamePhase.DAY_LAST_WORDS and to_phase == GamePhase.NIGHT_WEREWOLF:
            self.day += 1

        if self.phase == GamePhase.SETUP and to_phase == GamePhase.NIGHT_WEREWOLF:
            self.day = 1

        self.phase = to_phase

    def snapshot(self) -> dict[str, object]:
        return {
            "phase": self.phase.value,
            "day": self.day,
            "allowed_next": [p.value for p in self.allowed_next()],
        }
