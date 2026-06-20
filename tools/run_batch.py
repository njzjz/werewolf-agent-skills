#!/usr/bin/env python3
"""CLI for batch simulation regression."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPO_ROOT / "packages"
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from werewolf_core.batch import run_batch_simulations


def main() -> None:
    parser = argparse.ArgumentParser(description="Run deterministic batch simulations")
    parser.add_argument("--runs", type=int, default=20)
    parser.add_argument("--seed-start", type=int, default=1)
    parser.add_argument("--max-days", type=int, default=6)
    args = parser.parse_args()

    out = run_batch_simulations(runs=args.runs, seed_start=args.seed_start, max_days=args.max_days)
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
