#!/usr/bin/env python3
"""Judge orchestrator built on top of FSM + protocol validators + channels."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

from .channels import ChannelRegistry
from .fsm import GamePhase, WerewolfFSM
from .protocol import validate_judge_task, validate_player_reply, ValidationError


@dataclass
class AuditEvent:
    timestamp: str
    day: int
    phase: str
    actor: str
    event: str
    details: dict[str, Any] = field(default_factory=dict)


class JudgeOrchestrator:
    def __init__(
        self,
        *,
        players: list[str] | None = None,
        wolves: list[str] | None = None,
        audit_path: str | None = None,
    ) -> None:
        self.fsm = WerewolfFSM()
        self.players = players or []
        self.wolves = wolves or []
        self.channels = ChannelRegistry(wolves=self.wolves, players=self.players)
        self.audit_log: list[AuditEvent] = []
        self.audit_path = Path(audit_path) if audit_path else None

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _persist_audit(self) -> None:
        if self.audit_path is None:
            return
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)
        self.audit_path.write_text(self.snapshot_json(), encoding="utf-8")

    def _audit(self, actor: str, event: str, **details: Any) -> None:
        self.audit_log.append(
            AuditEvent(
                timestamp=self._now(),
                day=self.fsm.day,
                phase=self.fsm.phase.value,
                actor=actor,
                event=event,
                details=details,
            )
        )
        self._persist_audit()

    def phase_summary(self) -> dict[str, Any]:
        snapshot = self.fsm.snapshot()
        return {
            "phase": snapshot["phase"],
            "day": snapshot["day"],
            "allowed_actions": snapshot["allowed_next"],
            "next_step": snapshot["allowed_next"][0] if snapshot["allowed_next"] else None,
        }

    def transition(self, to_phase: GamePhase, actor: str = "judge") -> None:
        before = self.fsm.phase
        self.fsm.transition(to_phase)
        self._audit(
            actor=actor,
            event="phase_transition",
            from_phase=before.value,
            to_phase=to_phase.value,
            allowed_next=[p.value for p in self.fsm.allowed_next()],
        )

    def validate_judge_task_payload(self, payload: dict[str, Any], actor: str = "judge") -> dict[str, Any]:
        try:
            task = validate_judge_task(payload)
        except ValidationError as exc:
            self._audit(actor=actor, event="invalid_judge_task", error=str(exc))
            raise
        self._audit(actor=actor, event="judge_task_valid", target_player=task["player_id"], phase=task["phase"])
        return task

    def accept_player_reply(self, payload: dict[str, Any], actor: str, *, max_retries: int = 2) -> dict[str, Any]:
        attempts = 0
        while True:
            attempts += 1
            try:
                reply = validate_player_reply(payload)
            except ValidationError as exc:
                self._audit(actor=actor, event="invalid_player_reply", attempt=attempts, error=str(exc))
                if attempts > max_retries:
                    self._audit(actor="judge", event="player_reply_degraded", actor_id=actor, reason="max_retries_exceeded")
                    raise
                continue

            self._audit(actor=actor, event="player_reply_accepted", attempt=attempts, intent=reply["intent"])
            return reply

    def channel_write(self, channel: str, actor: str, payload: dict[str, Any]) -> None:
        ch = self.channels.get(channel)
        ch.write(actor=actor, phase=self.fsm.phase.value, payload=payload)
        self._audit(actor=actor, event="channel_write", channel=channel)

    def channel_read(self, channel: str, actor: str) -> list[dict[str, Any]]:
        ch = self.channels.get(channel)
        out = ch.read(actor=actor, phase=self.fsm.phase.value)
        self._audit(actor=actor, event="channel_read", channel=channel, count=len(out))
        return out

    def snapshot(self) -> dict[str, Any]:
        return {
            "fsm": self.fsm.snapshot(),
            "summary": self.phase_summary(),
            "audit_events": [
                {
                    "timestamp": e.timestamp,
                    "day": e.day,
                    "phase": e.phase,
                    "actor": e.actor,
                    "event": e.event,
                    "details": e.details,
                }
                for e in self.audit_log
            ],
        }

    def snapshot_json(self) -> str:
        return json.dumps(self.snapshot(), ensure_ascii=False, indent=2)
