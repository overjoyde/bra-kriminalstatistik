"""Offline-tester för brastat.watchlist (samlad CSV, ögonblicksbilder, behåll rader vid fel)."""
import datetime as dt
import gzip
import tempfile
import unittest
from pathlib import Path

from brastat.watchlist import COMBINED, PREVIOUS, SNAPSHOTS, read_csv, save_combined, snapshot, write_csv

FIELDS = ["serie", "period", "antal"]


class TestWatchlist(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.out = Path(self._tmp.name)

    def rows(self, serie, n, value="1"):
        return [{"serie": serie, "period": f"2026-{i + 1:02d}", "antal": value} for i in range(n)]

    def test_write_and_read_roundtrip_with_bom(self):
        p = self.out / "x.csv"
        write_csv(p, self.rows("a", 2) + [{"serie": "b", "period": "2026-01", "antal": "3", "extra": "ignoreras"}],
                  FIELDS)
        self.assertTrue(p.read_bytes().startswith(b"\xef\xbb\xbf"))
        rows = read_csv(p)
        self.assertEqual([r["serie"] for r in rows], ["a", "a", "b"])
        self.assertNotIn("extra", rows[0])

    def test_first_run_has_no_snapshot(self):
        save_combined(self.out, self.rows("a", 2), FIELDS)
        self.assertFalse((self.out / PREVIOUS).exists())
        self.assertEqual(len(read_csv(self.out / COMBINED)), 2)

    def test_second_run_keeps_previous_and_snapshot(self):
        save_combined(self.out, self.rows("a", 2), FIELDS)
        save_combined(self.out, self.rows("a", 3), FIELDS)
        self.assertEqual(len(read_csv(self.out / PREVIOUS)), 2)
        snaps = list((self.out / SNAPSHOTS).glob("watchlist_samlad_*.csv.gz"))
        self.assertEqual(len(snaps), 1)
        self.assertEqual(len(read_csv(snaps[0])), 2)
        with gzip.open(snaps[0], "rt", encoding="utf-8-sig") as f:
            self.assertTrue(f.readline().startswith("serie;"))

    def test_failed_series_keep_old_rows(self):
        save_combined(self.out, self.rows("a", 2) + self.rows("b", 4, "9"), FIELDS)
        with self.assertLogs("brastat.watchlist", "WARNING") as cm:
            save_combined(self.out, self.rows("a", 3), FIELDS, failed=["b"])
        self.assertIn("Behåller 4 rader", cm.output[0])
        rows = read_csv(self.out / COMBINED)
        self.assertEqual(sum(r["serie"] == "a" for r in rows), 3)
        self.assertEqual([r["antal"] for r in rows if r["serie"] == "b"], ["9"] * 4)

    def test_snapshot_pruning(self):
        p = self.out / COMBINED
        write_csv(p, self.rows("a", 1), FIELDS)
        for day in range(1, 6):
            snapshot(p, keep=3, today=dt.date(2026, 1, day))
        names = sorted(x.name for x in (self.out / SNAPSHOTS).iterdir())
        self.assertEqual(names, [f"watchlist_samlad_2026-01-0{d}.csv.gz" for d in (3, 4, 5)])

    def test_snapshot_of_missing_file(self):
        self.assertIsNone(snapshot(self.out / "finns-inte.csv"))


if __name__ == "__main__":
    unittest.main()
