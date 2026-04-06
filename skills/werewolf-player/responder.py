#!/usr/bin/env python3
"""Player responder entrypoint for werewolf-player skill.

Input: JudgeTask JSON from stdin
Output: PlayerReply JSON to stdout
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from packages.werewolf_core.protocol import validate_judge_task


def _pick_default_target(options: list[str], player_id: str) -> str | None:
    for opt in options:
        if opt != player_id:
            return opt
    return options[0] if options else None


def build_player_reply(task: dict[str, Any]) -> dict[str, Any]:
    intent = "speak"
    phase = task["phase"]

    if phase == "day_vote":
        intent = "vote"
    elif phase.startswith("night_"):
        intent = "night_action"

    target = _pick_default_target(task.get("action_options", []), task["player_id"])

    speech = "仅基于公开信息判断，先给出保守选择。"
    if intent == "vote":
        speech = f"当前信息有限，我暂投 {target}."
    elif intent == "night_action":
        speech = f"按本角色夜间职责，行动目标 {target}."

    return {
        "game_id": task["game_id"],
        "player_id": task["player_id"],
        "schema_version": task["schema_version"],
        "intent": intent,
        "content": {
            "speech": speech,
            "target": target,
            "confidence": 0.6,
        },
    }


def main() -> None:
    raw = sys.stdin.read().strip()
    if not raw:
        raise SystemExit("empty stdin")

    task = json.loads(raw)
    task = validate_judge_task(task)
    reply = build_player_reply(task)
    sys.stdout.write(json.dumps(reply, ensure_ascii=False))


if __name__ == "__main__":
    main()
