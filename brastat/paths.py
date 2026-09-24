"""Standardkataloger. Datakatalogen kan styras med miljövariabeln BRA_DATA_DIR."""
from __future__ import annotations

import os
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def data_dir(override: str | os.PathLike | None = None) -> Path:
    p = Path(override or os.environ.get("BRA_DATA_DIR") or REPO / "data")
    p.mkdir(parents=True, exist_ok=True)
    return p
