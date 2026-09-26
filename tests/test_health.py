"""Offline-tester för hälsokontrollen i brastat.health."""
import csv
import datetime as dt
import hashlib
import os
import tempfile
import unittest
from pathlib import Path

from brastat.health import check_certificate, check_domstat, check_manifest, check_revisions, check_sol, run_all
from brastat.http import EXTRA_CA
from brastat.watchlist import write_csv

FIELDS = ["group", "file", "url", "status", "bytes", "sha256", "note"]
TODAY = dt.date(2026, 9, 26)
NOW = dt.datetime(2026, 9, 26, 12)


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.data = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def add_file(self, rel: str, content: bytes = b"data") -> dict:
        p = self.data / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(content)
        return {"file": rel, "status": "ok", "bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()}

    def write_manifest(self, rows: list[dict], mtime: dt.datetime = NOW):
        p = self.data / "manifest.csv"
        with p.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            w.writeheader()
            for r in rows:
                w.writerow({k: r.get(k, "") for k in FIELDS})
        os.utime(p, (mtime.timestamp(), mtime.timestamp()))

    def manifest(self, **kw):
        kw.setdefault("expected_groups", ())
        return check_manifest(self.data, now=NOW, **kw)


class TestManifest(Base):
    def test_missing_manifest_is_error(self):
        f = self.manifest()
        self.assertEqual([(x.level, x.check) for x in f], [("error", "manifest")])

    def test_healthy_manifest(self):
        self.write_manifest([{"group": "anmalda", **self.add_file("raw/a.xlsx")},
                             {"group": "anmalda", **self.add_file("raw/b.xlsx"), "status": "cached"},
                             {"group": "amnessidor", **self.add_file("raw/c.csv"), "status": "extraherad"}])
        self.assertEqual(self.manifest(verify=True), [])

    def test_status_classification(self):
        ok = {"group": "anmalda", **self.add_file("raw/a.xlsx")}
        self.write_manifest([ok,
                             {"group": "anmalda", "url": "https://x/1", "status": "FEL: HTTP 404"},
                             {"group": "anmalda", "url": "https://x/2", "status": "saknas"},
                             {"group": "anmalda", "url": "https://x/3", "status": "konstig"}])
        got = sorted((x.level, x.check, x.message.split(":")[0]) for x in self.manifest())
        self.assertEqual(got, [("error", "status", "https"), ("error", "status", "https"),
                               ("warning", "status", "https")])
        self.assertTrue(any("FEL: HTTP 404" in x.message for x in self.manifest()))

    def test_empty_missing_and_corrupt_files(self):
        empty = {"group": "g", **self.add_file("raw/empty.xlsx"), "bytes": 0}
        gone = {"group": "g", **self.add_file("raw/gone.xlsx")}
        (self.data / "raw/gone.xlsx").unlink()
        corrupt = {"group": "g", **self.add_file("raw/corrupt.xlsx")}
        (self.data / "raw/corrupt.xlsx").write_bytes(b"changed")
        fine = {"group": "g", **self.add_file("raw/fine.xlsx")}
        self.write_manifest([empty, gone, corrupt, fine])
        self.assertEqual(sorted(x.check for x in self.manifest()), ["empty", "missing_file"])
        self.assertEqual(sorted(x.check for x in self.manifest(verify=True)), ["checksum", "empty", "missing_file"])

    def test_group_where_nothing_succeeded(self):
        self.write_manifest([{"group": "anmalda", **self.add_file("raw/a.xlsx")},
                             {"group": "lagforda", "url": "u1", "status": "saknas"},
                             {"group": "lagforda", "url": "u2", "status": "FEL: timeout"}])
        failed = [x for x in self.manifest() if x.check == "group_failed"]
        self.assertEqual([(x.level, x.group) for x in failed], [("error", "lagforda")])

    def test_expected_groups_and_age(self):
        self.write_manifest([{"group": "anmalda", **self.add_file("raw/a.xlsx")}], mtime=NOW - dt.timedelta(days=50))
        f = check_manifest(self.data, now=NOW, expected_groups=("anmalda", "misstankta"), max_age_days=40)
        self.assertEqual(sorted((x.level, x.check) for x in f),
                         [("warning", "group_missing"), ("warning", "manifest_age")])
        self.assertEqual(check_manifest(self.data, now=NOW, expected_groups=(), max_age_days=60), [])


class TestSolAndDomstat(Base):
    def write_sol(self, periods: list[str]):
        p = self.data / "sol" / "watchlist_samlad.csv"
        p.parent.mkdir(parents=True)
        with p.open("w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["serie", "period", "periodtyp", "antal"])
            for per in periods:
                w.writerow(["x", per, "manad", "12.0"])
            w.writerow(["x", "2026", "ar", "99.0"])  # årsrader ignoreras
            w.writerow(["x", "2026-09", "manad", ""])  # tomt värde räknas inte

    def test_sol_fresh_and_stale(self):
        self.write_sol(["2026-06", "2026-07"])
        self.assertEqual(check_sol(self.data, today=TODAY, max_lag_months=3), [])
        f = check_sol(self.data, today=TODAY, max_lag_months=1)
        self.assertEqual([(x.level, x.check) for x in f], [("warning", "sol_lag")])
        self.assertIn("2026-07", f[0].message)

    def test_sol_missing(self):
        self.assertEqual([x.check for x in check_sol(self.data, today=TODAY)], ["sol"])

    def test_domstat(self):
        self.assertEqual(check_domstat(self.data, today=TODAY), [])  # valfritt
        p = self.data / "domstat" / "watchlist_samlad.csv"
        p.parent.mkdir(parents=True)
        p.write_text("serie;ar;varde\nx;2021;1\nx;2022;2\n", encoding="utf-8-sig")
        self.assertEqual([x.check for x in check_domstat(self.data, today=TODAY)], ["domstat_lag"])
        self.assertEqual(check_domstat(self.data, today=dt.date(2024, 1, 1)), [])

    def test_run_all_combines(self):
        self.write_sol(["2026-08"])
        self.write_manifest([{"group": "anmalda", **self.add_file("raw/a.xlsx")}], mtime=NOW)
        f = run_all(self.data, today=TODAY)
        # Bara förväntade grupper som inte finns i manifestet ska flaggas
        self.assertEqual({x.check for x in f}, {"group_missing"})


SOL_FIELDS = ["serie", "brott_id", "brottskod", "omrade", "period", "periodtyp", "preliminar", "antal"]
DOM_FIELDS = ["serie", "tabell", "domstol", "dimension", "dimensionsvarde", "variabel", "ar", "varde"]


class TestRevisions(Base):
    def sol_rows(self, serie="pt", values=None, prelim="False"):
        values = values or {"2024-01": "100", "2024-02": "200"}
        return [{"serie": serie, "brott_id": "1", "brottskod": "", "omrade": "Hela landet", "period": per,
                 "periodtyp": "manad", "preliminar": prelim, "antal": v} for per, v in values.items()]

    def write(self, source, prev, cur, fields):
        write_csv(self.data / source / "watchlist_samlad.prev.csv", prev, fields)
        write_csv(self.data / source / "watchlist_samlad.csv", cur, fields)

    def test_no_previous_run(self):
        self.assertEqual(check_revisions(self.data, "sol"), [])

    def test_unchanged(self):
        self.write("sol", self.sol_rows(), self.sol_rows(), SOL_FIELDS)
        self.assertEqual(check_revisions(self.data, "sol"), [])

    def test_final_value_revised(self):
        self.write("sol", self.sol_rows(), self.sol_rows(values={"2024-01": "150", "2024-02": "201"}), SOL_FIELDS)
        f = check_revisions(self.data, "sol")
        self.assertEqual([x.check for x in f], ["sol_revised"])
        self.assertIn("100 -> 150", f[0].message)
        self.assertIn("1 slutliga", f[0].message)  # 200 -> 201 är under gränsen

    def test_preliminary_revisions_are_expected(self):
        prev = self.sol_rows(prelim="True")
        cur = self.sol_rows(values={"2024-01": "500", "2024-02": "900"}, prelim="True")
        self.write("sol", prev, cur, SOL_FIELDS)
        self.assertEqual(check_revisions(self.data, "sol"), [])

    def test_series_gone_and_rows_dropped(self):
        many = {f"2024-{m:02d}": "10" for m in range(1, 11)}
        prev = self.sol_rows("a", many) + self.sol_rows("b")
        cur = self.sol_rows("a", {"2024-01": "10", "2024-02": "10"})
        self.write("sol", prev, cur, SOL_FIELDS)
        self.assertEqual(sorted(x.check for x in check_revisions(self.data, "sol")),
                         ["sol_rows_dropped", "sol_series_gone"])

    def test_domstat_latest_year_may_change(self):
        def rows(v24, v25):
            base = {"serie": "k", "tabell": "t", "domstol": "Alla tingsrätter", "dimension": "", "dimensionsvarde": "",
                    "variabel": "Inkomna"}
            return [{**base, "ar": "2024", "varde": v24}, {**base, "ar": "2025", "varde": v25}]
        self.write("domstat", rows("100", "50"), rows("100", "90"), DOM_FIELDS)
        self.assertEqual(check_revisions(self.data, "domstat"), [])
        self.write("domstat", rows("100", "50"), rows("140", "90"), DOM_FIELDS)
        self.assertEqual([x.check for x in check_revisions(self.data, "domstat")], ["domstat_revised"])


class TestCertificate(unittest.TestCase):
    def test_bundled_certificate_valid_today(self):
        self.assertEqual(check_certificate(today=dt.date(2026, 9, 26)), [])

    def test_warns_before_expiry_and_errors_after(self):
        near = check_certificate(today=dt.date(2030, 3, 1))
        self.assertEqual([(x.level, x.check) for x in near], [("warning", "certificate")])
        self.assertIn("2030-07-02", near[0].message)
        self.assertEqual(check_certificate(today=dt.date(2031, 1, 1))[0].level, "error")

    def test_missing_certificate(self):
        self.assertEqual(check_certificate(EXTRA_CA.with_name("finns-inte.pem"))[0].check, "certificate")


if __name__ == "__main__":
    unittest.main()
