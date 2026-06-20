#!/usr/bin/env python3
"""Batch regression smoke tests."""

from werewolf_core.batch import run_batch_simulations


def test_batch_simulations_runs() -> None:
    out = run_batch_simulations(runs=5, seed_start=1, max_days=4)
    summary = out["summary"]

    assert summary["runs"] == 5
    assert isinstance(summary["winners"], dict)
    assert summary["avg_days"] >= 1
