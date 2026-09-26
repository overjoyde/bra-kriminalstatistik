"""Offline-tester för SOL-tolkningen (kör: python -m unittest discover -s tests)."""
import datetime as dt
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

from brastat.sol import SolClient, parse_catalog, parse_dbfil
from brastat.tabeller import default_last_full_year

FIX = ROOT / "tests" / "fixtures"


class FakeHttp:
    """Spelar upp sparade SOL-svar i stället för att gå mot nätet."""

    def __init__(self):
        self.urval = (FIX / "sol_urval_brottskod_manad.html").read_bytes()
        self.dbfil = (FIX / "sol_dbfil_manad.txt").read_text(encoding="utf-8").encode("latin-1")
        self.posts = []

    def get(self, url, referer=None):
        if "urval?menyid" in url:
            return self.urval
        return b"<html>ok</html>"

    def post(self, url, data, referer=None):
        self.posts.append((url, data))
        return self.dbfil if url.endswith("dbfil") else b"<html>ok</html>"


class TestCatalog(unittest.TestCase):
    def setUp(self):
        html = (FIX / "sol_urval_brottskod_manad.html").read_text(encoding="latin-1")
        self.cat = parse_catalog(html, "brottskod-manad-region")

    def test_crime_codes(self):
        c = self.cat.crime_by_code("0950")
        self.assertEqual(c.id, "13876")
        self.assertTrue(c.label.startswith("0950 - Befogenhetsbedrägeri"))
        self.assertEqual(self.cat.crime_by_code("950").code, "0950")

    def test_regions(self):
        self.assertEqual(self.cat.region_id("Hela landet"), "8291")
        with self.assertRaises(KeyError):
            self.cat.region_id("Atlantis")

    def test_periods(self):
        months = self.cat.select_periods("2026-01..2026-03")
        self.assertEqual([p.key for p in months], ["2026-01", "2026-02", "2026-03"])
        self.assertTrue(all(p.prel for p in months))
        latest = self.cat.select_periods("senaste")[0]
        self.assertEqual(latest.kind, "manad")
        self.assertEqual(latest.year, max(p.year for p in self.cat.periods))


class TestDbfil(unittest.TestCase):
    def test_parse_year_file(self):
        rows = parse_dbfil((FIX / "sol_dbfil_ar.txt").read_text(encoding="utf-8"))
        self.assertEqual(rows[0]["Region"], "Hela landet")
        bef = [r for r in rows if r["Brott"] == "Befogenhetsbedrägeri"]
        self.assertEqual([r["Antal"] for r in bef], ["13816", "14278"])


class TestQuery(unittest.TestCase):
    def test_query_offline(self):
        sol = SolClient(client=FakeHttp())
        rows = sol.query("brottskod-manad-region", codes=["0950"], regions=["Hela landet"],
                         periods="2025-01..2026-08")
        by = {(r["omrade"], r["period"]): r for r in rows}
        self.assertEqual(by[("Hela landet", "2026-08")]["antal"], 498.0)
        self.assertTrue(by[("Hela landet", "2026-08")]["preliminar"])
        self.assertFalse(by[("Hela landet", "2025-01")]["preliminar"])
        post = sol.http.posts[0][1]
        self.assertEqual(post["brottstyp_id_string"], "13876")
        self.assertEqual(post["region_id_string"], "8291")


class TestTabeller(unittest.TestCase):
    def test_last_full_year(self):
        self.assertEqual(default_last_full_year(dt.date(2026, 9, 24)), 2025)
        self.assertEqual(default_last_full_year(dt.date(2026, 2, 1)), 2024)


if __name__ == "__main__":
    unittest.main()
