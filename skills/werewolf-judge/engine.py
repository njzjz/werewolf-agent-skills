#!/usr/bin/env python3
"""Judge entrypoint for werewolf-judge skill.

This is intentionally thin: orchestrate via werewolf_core.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from packages.werewolf_core.fsm import GamePhase
from packages.werewolf_core.orchestrator import JudgeOrchestrator


def _build_orchestrator(args: argparse.Namespace) -> JudgeOrchestrator:
    players = [p.strip() for p in args.players.split(",") if p.strip()]
    wolves = [p.strip() for p in args.wolves.split(",") if p.strip()]
    return JudgeOrchestrator(
        players=players,
        wolves=wolves,
        audit_path=args.audit,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="werewolf-judge orchestrator entry")
    parser.add_argument("command", choices=["init", "next", "snapshot", "validate-task", "accept-reply"]) 
    parser.add_argument("--to", default="", help="target phase for next")
    parser.add_argument("--players", default="", help="comma-separated player ids")
    parser.add_argument("--wolves", default="", help="comma-separated wolf player ids")
    parser.add_argument(
        "--audit",
        default="skills/werewolf-judge/runtime/audit.json",
        help="audit snapshot output path",
    )
    parser.add_argument(
        "--payload",
        default="",
        help="inline JSON payload for validate-task/accept-reply",
    )
    args = parser.parse_args()

    # ensure default runtime dir exists when using default path
    Path(args.audit).parent.mkdir(parents=True, exist_ok=True)

    orchestrator = _build_orchestrator(args)

    if args.command == "init":
        orchestrator.transition(GamePhase.NIGHT_WEREWOLF)
        print(orchestrator.snapshot_json())
        return

    if args.command == "next":
        if not args.to:
            raise SystemExit("--to is required for command=next")
        orchestrator.transition(GamePhase(args.to))
        print(orchestrator.snapshot_json())
        return

    if args.command == "validate-task":
        if not args.payload:
            raise SystemExit("--payload is required for validate-task")
        payload = json.loads(args.payload)
        result = orchestrator.validate_judge_task_payload(payload)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if args.command == "accept-reply":
        if not args.payload:
            raise SystemExit("--payload is required for accept-reply")
        payload = json.loads(args.payload)
        result = orchestrator.accept_player_reply(payload, actor=payload.get("player_id", "unknown"))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if args.command == "snapshot":
        print(orchestrator.snapshot_json())


if __name__ == "__main__":
    main()
