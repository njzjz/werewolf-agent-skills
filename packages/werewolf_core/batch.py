#!/usr/bin/env python3
"""Batch simulation harness for regression checking."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from typing import Any

from .runner import simulate_game_6p


@dataclass
class BatchSummary:
    runs: int
    winners: dict[str, int]
    failures: int
    avg_days: float


def run_batch_simulations(
    *,
    runs: int = 20,
    seed_start: int = 1,
    max_days: int = 6,
) -> dict[str, Any]:
    if runs <= 0:
        raise ValueError("runs must be > 0")

    winners: dict[str, int] = {}
    failures = 0
    total_days = 0
    details: list[dict[str, Any]] = []

    for i in range(runs):
        seed = seed_start + i
        result = simulate_game_6p(seed=seed, max_days=max_days)
        details.append(result)

        winner = result.get("winner") or "UNKNOWN"
        winners[winner] = winners.get(winner, 0) + 1

        if winner == "超时平局":
            failures += 1

        total_days += int(result.get("days_played", 0))

    avg_days = total_days / runs

    return {
        "summary": BatchSummary(
            runs=runs,
            winners=winners,
            failures=failures,
            avg_days=avg_days,
        ).__dict__,
        "details": details,
    }


def main() -> None:
    """CLI entrypoint for deterministic batch regression simulations."""
    parser = argparse.ArgumentParser(description="Run deterministic batch simulations")
    parser.add_argument("--runs", type=int, default=20)
    parser.add_argument("--seed-start", type=int, default=1)
    parser.add_argument("--max-days", type=int, default=6)
    args = parser.parse_args()

    out = run_batch_simulations(runs=args.runs, seed_start=args.seed_start, max_days=args.max_days)
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
