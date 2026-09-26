"""Offline-tester för export till Parquet/DuckDB (hoppas över om pyarrow/duckdb saknas)."""
import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HAS_PANDAS = importlib.util.find_spec("pandas") is not None
HAS_PYARROW = importlib.util.find_spec("pyarrow") is not None
HAS_DUCKDB = importlib.util.find_spec("duckdb") is not None
FIX = Path(__file__).resolve().parent / "fixtures" / "analysis"


@unittest.skipUnless(HAS_PANDAS, "pandas saknas")
class TestExport(unittest.TestCase):
    def setUp(self):
        from brastat.analysis import parse_bra as pb
        from brastat.cli import export_data

        self.export_data = export_data
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.data = Path(self._tmp.name)
        (self.data / "domstat").mkdir()
        shutil.copy(FIX / "domstat_watchlist.csv", self.data / "domstat" / "watchlist_samlad.csv")
        # Brås råfiler finns inte i testet -> tabellerna ska hoppas över, inte krascha.
        for name in ("monthly", "annual", "suspects"):
            p = mock.patch.object(pb, name, side_effect=FileNotFoundError(name))
            p.start()
            self.addCleanup(p.stop)

    def test_tables_skip_missing_sources(self):
        with mock.patch.object(self.export_data, "log"):
            counts = self.export_data.export(self.data, self.data / "export", formats=[])
        self.assertEqual(counts, {"domstat_watchlist": 90})

    @unittest.skipUnless(HAS_PYARROW, "pyarrow saknas")
    def test_parquet(self):
        import pandas as pd

        self.export_data.export(self.data, self.data / "export", ["parquet"])
        df = pd.read_parquet(self.data / "export" / "domstat_watchlist.parquet")
        self.assertEqual(len(df), 90)
        self.assertEqual(df["dimensionsvarde"].dtype.kind, "O")

    @unittest.skipUnless(HAS_DUCKDB, "duckdb saknas")
    def test_duckdb(self):
        import duckdb

        self.export_data.export(self.data, self.data / "export", ["duckdb"])
        con = duckdb.connect(str(self.data / "export" / "brastat.duckdb"), read_only=True)
        try:
            n = con.execute("SELECT count(*) FROM domstat_watchlist").fetchone()[0]
        finally:
            con.close()
        self.assertEqual(n, 90)


if __name__ == "__main__":
    unittest.main()
