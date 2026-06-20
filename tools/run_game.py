#!/usr/bin/env python3
"""Thin CLI wrapper for the formal werewolf_core runner."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPO_ROOT / "packages"
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from werewolf_core.runner import main

if __name__ == "__main__":
    main()
