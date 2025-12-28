"""Pytest configuration.

This repository is intentionally lightweight early on and does not yet package
itself as an installable distribution. For now, tests import project modules by
adding the repository root to `sys.path`.
"""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
