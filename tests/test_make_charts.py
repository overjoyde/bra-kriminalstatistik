"""Offline-tester för de rena funktionerna i brastat.analysis.charts (prognos och årstabell)."""
import tempfile
import unittest
from pathlib import Path

try:
    import numpy as np
    import pandas as pd

    from brastat.analysis import charts as mc
except ImportError:  # pandas/matplotlib saknas
    mc = None


def synthetic(months: int = 72, level: float = 1000.0, slope: float = 5.0, noise: float = 0.0, seed: int = 1):
    """Månadsserie med linjär trend och multiplikativ säsong (topp i december)."""
    idx = pd.date_range("2019-01-01", periods=months, freq="MS")
    season = 1 + 0.2 * np.cos(2 * np.pi * (idx.month - 12) / 12)
    rng = np.random.default_rng(seed)
    values = (level + slope * np.arange(months)) * season * np.exp(rng.normal(0, noise, months))
    return pd.Series(values, idx), season


@unittest.skipIf(mc is None, "pandas/matplotlib saknas")
class TestSeasonalForecast(unittest.TestCase):
    def test_shape_and_index(self):
        s, _ = synthetic(noise=0.03)
        f, lo, hi = mc.seasonal_forecast(s, h=6)
        self.assertEqual(len(f), 6)
        self.assertEqual(f.index[0], pd.Timestamp("2025-01-01"))  # månaden efter sista observationen
        self.assertEqual(list(f.index), list(pd.date_range("2025-01-01", periods=6, freq="MS")))
        self.assertTrue(f.index.equals(lo.index) and f.index.equals(hi.index))

    def test_interval_brackets_forecast_and_widens(self):
        s, _ = synthetic(noise=0.05)
        f, lo, hi = mc.seasonal_forecast(s, h=6)
        self.assertTrue((lo <= f).all() and (f <= hi).all())
        width = (hi - lo) / f
        self.assertTrue(width.is_monotonic_increasing, "intervallet ska vidgas med horisonten (sqrt(h))")

    def test_recovers_trend_and_season_without_noise(self):
        s, _ = synthetic(months=84, noise=0.0)
        f, _, _ = mc.seasonal_forecast(s, h=12)
        # Facit: fortsätt den syntetiska serien 12 månader till
        full, _ = synthetic(months=96, noise=0.0)
        truth = full[-12:]
        rel_err = ((f.values - truth.values) / truth.values)
        self.assertLess(np.abs(rel_err).max(), 0.05)
        self.assertEqual(f.idxmax().month, 12)  # säsongstoppen hamnar i december

    def test_ignores_missing_values(self):
        s, _ = synthetic(noise=0.02)
        s.iloc[10] = np.nan
        f, lo, hi = mc.seasonal_forecast(s, h=3)
        self.assertFalse(f.isna().any() or lo.isna().any() or hi.isna().any())


@unittest.skipIf(mc is None, "pandas/matplotlib saknas")
class TestAnnualTable(unittest.TestCase):
    def setUp(self):
        rows = []
        for year in range(2017, 2026):  # 9 år; tabellen ska visa de senaste 7
            rows.append({"Serie": "Penningtvättsbrott, totalt", "År": year, "Antal": 1000 * (year - 2016)})
            rows.append({"Serie": "Romansbedrägeri", "År": year, "Antal": 1500})
        rows.append({"Serie": "Ej med i tabellen", "År": 2025, "Antal": 1})
        self.annual = pd.DataFrame(rows)
        self.sol = pd.DataFrame([
            {"serie": "terrorfinansiering", "omrade": "Hela landet", "periodtyp": "ar", "brottskod": "7035",
             "brott": "Lag (2022:666) - Finansiering av terroristbrott", "ar": year, "antal": n}
            for year, n in ((2018, 9), (2023, 3), (2024, 1), (2025, 3))
        ] + [{"serie": "terrorfinansiering", "omrade": "Region Syd", "periodtyp": "ar", "brottskod": "7035",
              "brott": "x - y", "ar": 2025, "antal": 100}])

    def render(self) -> str:
        with tempfile.TemporaryDirectory() as d:
            mc.annual_table(self.sol, self.annual, Path(d))
            return (Path(d) / "arstabell.md").read_text(encoding="utf-8")

    def test_main_table(self):
        lines = self.render().splitlines()
        self.assertEqual(lines[0], "| Brottstyp | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | Förändring |")
        self.assertEqual(lines[1], "|---|" + "---:|" * 8)
        body = lines[2:lines.index("")]
        names = [row.split(" | ")[0].lstrip("| ") for row in body]
        # Alla serier i den fasta listan, i den ordningen; serier utanför listan tas inte med
        self.assertEqual(len(body), 11)
        self.assertEqual(names[0], "Bedrägeri och annan oredlighet")
        self.assertLess(names.index("Romansbedrägeri"), names.index("Penningtvättsbrott, totalt"))
        self.assertNotIn("Ej med i tabellen", names)
        pt = body[names.index("Penningtvättsbrott, totalt")]
        romans = body[names.index("Romansbedrägeri")]
        # Tusentalsavgränsare (smalt hårt mellanslag) och förändring första -> sista visade år
        self.assertIn("| 3\u202f000 |", pt)
        self.assertTrue(pt.endswith("| +200% (2019–2025) |"))
        self.assertTrue(romans.endswith("| +0% (2019–2025) |"))
        # Serie som saknas i datan ger en rad med streck i stället för krasch
        self.assertEqual(body[0], "| Bedrägeri och annan oredlighet | " + " | ".join(["–"] * 7) + " |  |")

    def test_ctf_table_uses_national_rows_from_2019(self):
        text = self.render()
        ctf = text.split("\n\n", 1)[1].splitlines()
        self.assertEqual(ctf[0], "| Kod | Brott | 2023 | 2024 | 2025 |")  # 2018 filtreras bort
        self.assertEqual(ctf[2], "| 7035 | Finansiering av terroristbrott | 3 | 1 | 3 |")  # regionrad ej summerad


if __name__ == "__main__":
    unittest.main()
