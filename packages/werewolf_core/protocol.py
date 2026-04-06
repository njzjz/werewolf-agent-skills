#!/usr/bin/env python3
"""Protocol validation for judge/player payloads.

Lightweight JSON-schema-like validation without external deps.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ValidationError(ValueError):
    code: str
    message: str

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"


ALLOWED_INTENTS = {"speak", "vote", "night_action"}
ALLOWED_PHASES = {
    "setup",
    "night_werewolf",
    "night_seer",
    "night_witch",
    "day_announce",
    "day_speech",
    "day_vote",
    "day_last_words",
    "game_over",
}

_JUDGE_TASK_REQUIRED = {
    "game_id",
    "phase",
    "player_id",
    "schema_version",
    "visible_context",
    "action_options",
    "deadline_s",
}

_PLAYER_REPLY_REQUIRED = {
    "game_id",
    "player_id",
    "schema_version",
    "intent",
    "content",
}

_PLAYER_REPLY_CONTENT_ALLOWED = {"speech", "target", "confidence"}


def _err(code: str, message: str) -> ValidationError:
    return ValidationError(code=code, message=message)


def _require_dict(payload: Any, name: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise _err("E_TYPE", f"{name} must be an object")
    return payload


def _require_str(payload: dict[str, Any], key: str, *, code: str = "E_FIELD") -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise _err(code, f"{key} must be a non-empty string")
    return value


def _optional_str(payload: dict[str, Any], key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise _err("E_FIELD", f"{key} must be a string when present")
    return value


def _require_list(payload: dict[str, Any], key: str) -> list[Any]:
    value = payload.get(key)
    if not isinstance(value, list):
        raise _err("E_FIELD", f"{key} must be a list")
    return value


def _reject_unknown_keys(payload: dict[str, Any], allowed: set[str], name: str) -> None:
    unknown = sorted(set(payload.keys()) - allowed)
    if unknown:
        raise _err("E_UNKNOWN_FIELD", f"{name} has unknown fields: {unknown}")


def validate_judge_task(payload: Any) -> dict[str, Any]:
    """Validate JudgeTask payload and return normalized dict.

    Error codes:
    - E_TYPE
    - E_FIELD
    - E_PHASE
    - E_UNKNOWN_FIELD
    """
    data = _require_dict(payload, "JudgeTask")
    _reject_unknown_keys(data, _JUDGE_TASK_REQUIRED, "JudgeTask")

    for key in _JUDGE_TASK_REQUIRED - {"visible_context", "action_options", "deadline_s"}:
        _require_str(data, key)

    phase = data["phase"]
    if phase not in ALLOWED_PHASES:
        raise _err("E_PHASE", f"phase must be one of {sorted(ALLOWED_PHASES)}")

    if "visible_context" not in data:
        raise _err("E_FIELD", "visible_context is required")
    visible_context = _require_dict(data["visible_context"], "visible_context")

    action_options = _require_list(data, "action_options")
    if not action_options:
        raise _err("E_FIELD", "action_options cannot be empty")
    if not all(isinstance(v, str) and v.strip() for v in action_options):
        raise _err("E_FIELD", "action_options items must be non-empty strings")

    deadline_s = data.get("deadline_s")
    if not isinstance(deadline_s, int) or deadline_s <= 0:
        raise _err("E_FIELD", "deadline_s must be a positive integer")

    # Keep explicit reference to the validated object for readability/future hooks.
    _ = visible_context
    return data


def validate_player_reply(payload: Any) -> dict[str, Any]:
    """Validate PlayerReply payload and return normalized dict.

    Error codes:
    - E_TYPE
    - E_FIELD
    - E_INTENT
    - E_UNKNOWN_FIELD
    """
    data = _require_dict(payload, "PlayerReply")
    _reject_unknown_keys(data, _PLAYER_REPLY_REQUIRED, "PlayerReply")

    for key in _PLAYER_REPLY_REQUIRED - {"content"}:
        _require_str(data, key)

    intent = data["intent"]
    if intent not in ALLOWED_INTENTS:
        raise _err("E_INTENT", f"intent must be one of {sorted(ALLOWED_INTENTS)}")

    if "content" not in data:
        raise _err("E_FIELD", "PlayerReply.content is required")
    content = _require_dict(data["content"], "content")
    _reject_unknown_keys(content, _PLAYER_REPLY_CONTENT_ALLOWED, "PlayerReply.content")

    _optional_str(content, "speech")
    _optional_str(content, "target")

    confidence = content.get("confidence")
    if confidence is not None:
        if not isinstance(confidence, (int, float)):
            raise _err("E_FIELD", "content.confidence must be number when present")
        if confidence < 0 or confidence > 1:
            raise _err("E_FIELD", "content.confidence must be in [0,1]")

    return data
