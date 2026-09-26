"""Gemensamt för bevakningslistorna (SOL och DOMstat): skriva CSV, ögonblicksbilder och robust sammanslagning.

Varje körning skriver ``watchlist_samlad.csv``. Innan den skrivs över sparas den förra versionen som

- ``watchlist_samlad.prev.csv`` – jämförs av hälsokontrollen (``brastat.health.check_revisions``)
- ``snapshots/watchlist_samlad_<ÅÅÅÅ-MM-DD>.csv.gz`` – daterade ögonblicksbilder för att följa hur
  preliminär statistik revideras över tid (de ``keep`` senaste behålls)

Om en serie misslyckas behålls dess rader från förra körningen, så att ett tillfälligt fel hos
källan inte tömmer den samlade filen.
"""

from __future__ import annotations

import csv
import datetime as dt
import gzip
import logging
import shutil
from pathlib import Path

log = logging.getLogger(__name__)

COMBINED = "watchlist_samlad.csv"
PREVIOUS = "watchlist_samlad.prev.csv"
SNAPSHOTS = "snapshots"


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter=";", extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def read_csv(path: Path) -> list[dict]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f, delimiter=";"))


def snapshot(path: Path, keep: int = 24, today: dt.date | None = None) -> Path | None:
    """Spara nuvarande fil som .prev.csv och som daterad .csv.gz. Returnerar ögonblicksbilden."""
    if not path.exists():
        return None
    shutil.copy2(path, path.with_name(PREVIOUS))
    snapdir = path.parent / SNAPSHOTS
    snapdir.mkdir(exist_ok=True)
    stamp = dt.datetime.fromtimestamp(path.stat().st_mtime).date() if today is None else today
    snap = snapdir / f"{path.stem}_{stamp:%Y-%m-%d}.csv.gz"
    with path.open("rb") as src, gzip.open(snap, "wb") as dst:
        shutil.copyfileobj(src, dst)
    for old in sorted(snapdir.glob(f"{path.stem}_*.csv.gz"))[: -keep or None]:
        old.unlink()
    return snap


def save_combined(
    out: Path, rows: list[dict], fields: list[str], failed: list[str] | None = None, keep: int = 24
) -> Path:
    """Skriv den samlade filen. Serier i ``failed`` får sina rader från förra körningen."""
    path = out / COMBINED
    kept: list[dict] = []
    if failed and path.exists():
        kept = [r for r in read_csv(path) if r.get("serie") in set(failed)]
        if kept:
            log.warning("Behåller %d rader från förra körningen för: %s", len(kept), ", ".join(sorted(failed)))
    snapshot(path, keep=keep)
    write_csv(path, rows + kept, fields)
    return path
