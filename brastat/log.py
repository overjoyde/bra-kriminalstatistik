"""Loggning för kommandoradsverktygen.

Biblioteket loggar via ``logging.getLogger("brastat.…")`` och sätter aldrig upp egna handlers.
Kommandona anropar :func:`setup` som skriver till stderr:

- i en terminal: bara meddelandet (som tidigare ``print``)
- annars (cron, launchd, Schemaläggaren, CI): med tidsstämpel och nivå, så att loggfilen går att följa

Miljövariabeln ``BRASTAT_LOG_TIMESTAMPS=1``/``0`` tvingar fram respektive stänger av tidsstämplar.
Data (CSV till stdout, katalogsökningar, rapporter) skrivs fortfarande med ``print``.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys

PLAIN = "%(message)s"
STAMPED = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"


def add_arguments(ap: argparse.ArgumentParser) -> None:
    g = ap.add_argument_group("loggning")
    g.add_argument("-v", "--verbose", action="count", default=0, help="Mer loggning (-v = DEBUG)")
    g.add_argument("-q", "--quiet", action="count", default=0, help="Mindre loggning (-q = bara varningar)")


def setup(verbose: int = 0, quiet: int = 0, stream=None) -> None:
    stream = stream or sys.stderr
    level = logging.INFO - 10 * verbose + 10 * quiet
    env = os.environ.get("BRASTAT_LOG_TIMESTAMPS")
    stamped = env == "1" if env in ("0", "1") else not (hasattr(stream, "isatty") and stream.isatty())
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter(STAMPED if stamped else PLAIN, "%Y-%m-%d %H:%M:%S"))
    root = logging.getLogger("brastat")
    root.handlers[:] = [handler]
    root.setLevel(max(logging.DEBUG, min(level, logging.CRITICAL)))
    root.propagate = False


def setup_from_args(a: argparse.Namespace) -> None:
    setup(getattr(a, "verbose", 0), getattr(a, "quiet", 0))
