#!/usr/bin/env python3
"""Exportera hämtad data till Parquet och/eller DuckDB för analys i t.ex. DuckDB, Polars, Power BI eller R.

    python scripts/export_data.py                         # Parquet -> data/export/*.parquet
    python scripts/export_data.py --format duckdb         # en DuckDB-fil -> data/export/brastat.duckdb
    python scripts/export_data.py --format parquet duckdb --out D:/analys

Tabeller (de som finns hämtade tas med, övriga hoppas över):
    sol_watchlist        SOL-bevakningslistan (långt format)
    domstat_watchlist    DOMstat-bevakningslistan (långt format)
    bra_manad            anmälda brott per månad och region (Brås tidsserier, tolkade)
    bra_ar               slutlig årsstatistik, tabell 100
    bra_misstankta       misstänkta personer efter ålder och kön, tabell 220

Kräver pandas samt pyarrow (Parquet) och/eller duckdb:  pip install -e ".[export]"
"""
from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Callable
from pathlib import Path

from brastat import log as blog
from brastat.paths import data_dir

log = logging.getLogger("brastat.export_data")


def tables(d: Path) -> dict[str, Callable]:
    """Tabellnamn -> funktion som returnerar en DataFrame (eller kastar om källan saknas)."""
    import pandas as pd

    from brastat.analysis import parse_bra as pb

    def csv(rel: str, **kw) -> Callable:
        def load():
            return pd.read_csv(d / rel, sep=";", encoding="utf-8-sig", **kw)
        return load

    return {
        "sol_watchlist": csv("sol/watchlist_samlad.csv", dtype={"brottskod": str, "brott_id": str}),
        "domstat_watchlist": csv("domstat/watchlist_samlad.csv", dtype={"dimension": str, "dimensionsvarde": str}),
        "bra_manad": pb.monthly,
        "bra_ar": pb.annual,
        "bra_misstankta": pb.suspects,
    }


def export(d: Path, out: Path, formats: list[str]) -> dict[str, int]:
    """Exportera alla tillgängliga tabeller. Returnerar tabell -> antal rader."""
    out.mkdir(parents=True, exist_ok=True)
    frames = {}
    for name, load in tables(d).items():
        try:
            df = load()
        except (FileNotFoundError, ValueError, KeyError, IndexError) as e:
            log.info("  - %s: hoppar över (%s)", name, e.__class__.__name__)
            continue
        if df.empty:
            log.info("  - %s: tom, hoppar över", name)
            continue
        frames[name] = df
    if "parquet" in formats:
        for name, df in frames.items():
            p = out / f"{name}.parquet"
            df.to_parquet(p, index=False)
            log.info("  + %s (%d rader)", p, len(df))
    if "duckdb" in formats:
        import duckdb

        p = out / "brastat.duckdb"
        con = duckdb.connect(str(p))
        try:
            for name, df in frames.items():
                con.register("_df", df)
                con.execute(f'CREATE OR REPLACE TABLE "{name}" AS SELECT * FROM _df')
                con.unregister("_df")
        finally:
            con.close()
        log.info("  + %s (%d tabeller)", p, len(frames))
    return {k: len(v) for k, v in frames.items()}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--format", nargs="+", choices=["parquet", "duckdb"], default=["parquet"])
    ap.add_argument("--data-dir", help="Datakatalog (standard: data/ eller BRA_DATA_DIR)")
    ap.add_argument("--out", help="Utkatalog (standard: <data>/export)")
    blog.add_arguments(ap)
    a = ap.parse_args()
    blog.setup_from_args(a)
    try:
        import pandas  # noqa: F401
        if "parquet" in a.format:
            import pyarrow  # noqa: F401
        if "duckdb" in a.format:
            import duckdb  # noqa: F401
    except ImportError as e:
        log.error("%s saknas – installera med: pip install -e \".[export]\"", e.name)
        sys.exit(2)
    d = data_dir(a.data_dir, create=False)
    counts = export(d, Path(a.out) if a.out else d / "export", a.format)
    if not counts:
        log.error("Ingen data att exportera i %s – kör fetch_all först.", d)
        sys.exit(1)


if __name__ == "__main__":
    main()
