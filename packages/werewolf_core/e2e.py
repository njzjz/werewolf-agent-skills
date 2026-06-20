#!/usr/bin/env python3
"""Backward-compatible import for deterministic e2e simulations.

Gameplay flow now lives in :mod:`werewolf_core.runner`; this module remains so
existing tests and callers can keep importing ``simulate_game_6p`` while the
formal package boundary moves away from ad-hoc e2e scripts.
"""

from __future__ import annotations

from .runner import simulate_game_6p

__all__ = ["simulate_game_6p"]
