"""Kataloger och paketresurser.

Datakatalogen väljs i den här ordningen:

1. uttryckligt argument (t.ex. ``--data-dir``)
2. miljövariabeln ``BRA_DATA_DIR``
3. ``data/`` i repot – när paketet körs från en utcheckning (``pip install -e .`` eller direkt)
4. användarens datakatalog när paketet är installerat som vanligt paket:
   macOS ``~/Library/Application Support/brastat``, Windows ``%LOCALAPPDATA%\\brastat``,
   annars ``$XDG_DATA_HOME/brastat`` (standard ``~/.local/share/brastat``)
"""

from __future__ import annotations

import os
import sys
from importlib import resources
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
REPO = PACKAGE.parent


def is_source_checkout() -> bool:
    """Sant när paketet ligger i en utcheckning av repot (inte i site-packages)."""
    return (REPO / "pyproject.toml").is_file() and (REPO / "brastat").resolve() == PACKAGE


def user_data_dir() -> Path:
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "brastat"
    if os.name == "nt":
        return Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local") / "brastat"
    return Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share") / "brastat"


def data_dir(override: str | os.PathLike | None = None, *, create: bool = True) -> Path:
    """Datakatalogen (se modulens docstring). ``create=False`` för läsare som inte ska skapa något."""
    if override or os.environ.get("BRA_DATA_DIR"):
        p = Path(override or os.environ["BRA_DATA_DIR"])
    elif is_source_checkout():
        p = REPO / "data"
    else:
        p = user_data_dir()
    if create:
        p.mkdir(parents=True, exist_ok=True)
    return p


def config_path(name: str) -> Path:
    """Sökväg till en medföljande bevakningslista i ``brastat/config``."""
    return Path(str(resources.files("brastat") / "config" / name))
