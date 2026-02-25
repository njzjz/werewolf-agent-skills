#!/usr/bin/env python3
"""Programmatic communication channels with ACL + phase checks."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class ChannelAccessError(PermissionError):
    """Raised on unauthorized channel access."""


@dataclass
class Message:
    actor: str
    phase: str
    payload: dict[str, Any]


@dataclass
class Channel:
    name: str
    readable_by: set[str] = field(default_factory=set)
    writable_by: set[str] = field(default_factory=set)
    readable_phases: set[str] | None = None
    writable_phases: set[str] | None = None
    logs: list[Message] = field(default_factory=list)

    def _check_role(self, actor: str, allowed: set[str], action: str) -> None:
        if actor not in allowed:
            raise ChannelAccessError(
                f"{actor} cannot {action} channel={self.name}; allowed={sorted(allowed)}"
            )

    def _check_phase(self, phase: str, allowed: set[str] | None, action: str) -> None:
        if allowed is not None and phase not in allowed:
            raise ChannelAccessError(
                f"phase={phase} cannot {action} channel={self.name}; allowed={sorted(allowed)}"
            )

    def write(self, actor: str, phase: str, payload: dict[str, Any]) -> None:
        self._check_role(actor, self.writable_by, "write")
        self._check_phase(phase, self.writable_phases, "write")
        self.logs.append(Message(actor=actor, phase=phase, payload=payload))

    def read(self, actor: str, phase: str) -> list[dict[str, Any]]:
        self._check_role(actor, self.readable_by, "read")
        self._check_phase(phase, self.readable_phases, "read")
        return [m.payload for m in self.logs]


class ChannelRegistry:
    """Build and manage standard werewolf channels."""

    def __init__(self, wolves: list[str], players: list[str]):
        self.channels: dict[str, Channel] = {}

        # Public channel: day phases only.
        self.channels["public"] = Channel(
            name="public",
            readable_by=set(players) | {"judge", "main"},
            writable_by=set(players) | {"judge"},
            readable_phases={"day_announce", "day_speech", "day_vote", "day_last_words", "game_over"},
            writable_phases={"day_announce", "day_speech", "day_vote", "day_last_words", "game_over"},
        )

        # Wolf private channel: night werewolf phase only.
        self.channels["wolf_private"] = Channel(
            name="wolf_private",
            readable_by=set(wolves) | {"judge"},
            writable_by=set(wolves) | {"judge"},
            readable_phases={"night_werewolf"},
            writable_phases={"night_werewolf"},
        )

        # Night actions channel: all private night actions, judge-only read.
        self.channels["night_actions"] = Channel(
            name="night_actions",
            readable_by={"judge"},
            writable_by=set(players) | {"judge"},
            readable_phases={"night_werewolf", "night_seer", "night_witch"},
            writable_phases={"night_werewolf", "night_seer", "night_witch"},
        )

    def get(self, name: str) -> Channel:
        if name not in self.channels:
            raise KeyError(f"unknown channel: {name}")
        return self.channels[name]
