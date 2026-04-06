#!/usr/bin/env python3
"""Protocol validation smoke tests."""

from packages.werewolf_core.protocol import ValidationError, validate_judge_task, validate_player_reply


def test_validate_judge_task_ok() -> None:
    payload = {
        "game_id": "g1",
        "phase": "day_speech",
        "player_id": "p1",
        "schema_version": "v1",
        "visible_context": {"public": []},
        "action_options": ["p2", "p3"],
        "deadline_s": 30,
    }
    out = validate_judge_task(payload)
    assert out["phase"] == "day_speech"


def test_validate_judge_task_missing_visible_context_is_field_error() -> None:
    payload = {
        "game_id": "g1",
        "phase": "day_speech",
        "player_id": "p1",
        "schema_version": "v1",
        "action_options": ["p2", "p3"],
        "deadline_s": 30,
    }
    try:
        validate_judge_task(payload)
        assert False, "should fail"
    except ValidationError as exc:
        assert exc.code == "E_FIELD"


def test_validate_player_reply_rejects_unknown_field() -> None:
    payload = {
        "game_id": "g1",
        "player_id": "p1",
        "schema_version": "v1",
        "intent": "speak",
        "content": {"speech": "hi", "confidence": 0.5, "hack": True},
    }
    try:
        validate_player_reply(payload)
        assert False, "should fail"
    except ValidationError as exc:
        assert exc.code == "E_UNKNOWN_FIELD"


def test_validate_player_reply_missing_content_is_field_error() -> None:
    payload = {
        "game_id": "g1",
        "player_id": "p1",
        "schema_version": "v1",
        "intent": "speak",
    }
    try:
        validate_player_reply(payload)
        assert False, "should fail"
    except ValidationError as exc:
        assert exc.code == "E_FIELD"
