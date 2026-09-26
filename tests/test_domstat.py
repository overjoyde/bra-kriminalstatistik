"""Offline-tester för DOMstat-klienten (kör: python -m unittest discover -s tests)."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

from brastat.domstat import DomstatClient, build_query, norm_table, parse_metadata, parse_result, select_years
from brastat.paths import config_path

FIX = ROOT / "tests" / "fixtures"
TABLE = "AntalMal/02b_Malutveckling_per_malkategori_arenden_TR"


def load(name):
    return json.loads((FIX / name).read_text(encoding="utf-8"))


class FakeHttp:
    """Spelar upp sparade PxWeb-svar i stället för att gå mot nätet."""

    def __init__(self):
        self.posts = []

    def get(self, url, referer=None):
        if url.endswith(".px"):
            return json.dumps(load("domstat_meta_arenden_tr.json")).encode("utf-8")
        if url.endswith("/DOMstat"):
            return json.dumps([{"id": "AntalMal", "type": "l", "text": "Antal mål"}]).encode("utf-8")
        return json.dumps([{"id": "09_Konkurser_TR.px", "type": "t", "text": "Konkurser",
                            "updated": "2026-03-09"}]).encode("utf-8")

    def post_json(self, url, payload, referer=None):
        self.posts.append((url, payload))
        return json.dumps(load("domstat_result_arenden_tr.json")).encode("utf-8")


class TestMetadata(unittest.TestCase):
    def setUp(self):
        self.t = parse_metadata(TABLE, load("domstat_meta_arenden_tr.json"))

    def test_norm_table(self):
        self.assertEqual(norm_table("AntalMal/09_Konkurser_TR"), "/AntalMal/09_Konkurser_TR.px")
        self.assertEqual(norm_table("/AntalMal/09_Konkurser_TR.px/"), "/AntalMal/09_Konkurser_TR.px")

    def test_resolve_swedish_text_to_code(self):
        dom = self.t.var("Domstol")
        self.assertEqual(dom.resolve("Alla tingsrätter"), "All district courts")
        self.assertEqual(dom.resolve("alla TINGSRÄTTER"), "All district courts")
        self.assertEqual(dom.resolve("Attunda"), "Attunda")  # unikt delord räcker
        self.assertEqual(self.t.var("Målkategori").resolve("Skuldsanering"), "Debt clearance matters")
        with self.assertRaises(KeyError):
            dom.resolve("Atlantis")

    def test_years(self):
        yr = self.t.time_var
        self.assertEqual(yr.texts[0], "2002")
        self.assertEqual([yr.text_of(c) for c in select_years(yr, "2024-2025")], ["2024", "2025"])
        self.assertEqual([yr.text_of(c) for c in select_years(yr, "senaste:2")], ["2024", "2025"])
        self.assertEqual(len(select_years(yr, "alla")), len(yr.values))
        self.assertEqual([yr.text_of(c) for c in select_years(yr, "2024,2025")], ["2024", "2025"])
        self.assertEqual(yr.text_of(select_years(yr, "2025-")[0]), "2025")
        with self.assertRaises(ValueError):
            select_years(yr, "1850")

    def test_years_edge_cases(self):
        yr = self.t.time_var
        txt = lambda spec: [yr.text_of(c) for c in select_years(yr, spec)]  # noqa: E731
        # Öppna intervall, med och utan mellanslag
        self.assertEqual(txt("2015-"), [str(y) for y in range(2015, 2026)])
        self.assertEqual(txt(" 2024 - "), ["2024", "2025"])
        self.assertEqual(txt("-2003"), ["2002", "2003"])
        # senaste:N, även större än antalet år
        self.assertEqual(txt("senaste:3"), ["2023", "2024", "2025"])
        self.assertEqual(txt("SENASTE"), ["2025"])
        self.assertEqual(len(select_years(yr, "senaste:999")), len(yr.values))
        # Heltal och listor (även av heltal)
        self.assertEqual(txt(2025), ["2025"])
        self.assertEqual(txt([2024, "2025"]), ["2024", "2025"])
        self.assertEqual(select_years(yr, None), list(yr.values))
        self.assertEqual(select_years(yr, "*"), list(yr.values))
        # Urval utan träff ger fel i stället för en tom fråga
        for bad in ("senaste:0", "1990-1995", "2030-", [1850], "abc"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                select_years(yr, bad)

    def test_build_query_defaults_to_all_values(self):
        q = build_query(self.t, {"Domstol": "Alla tingsrätter"}, years="senaste")
        sel = {x["code"]: x["selection"]["values"] for x in q["query"]}
        self.assertEqual(sel["Domstol"], ["All district courts"])
        self.assertEqual(len(sel["Målkategori"]), len(self.t.var("Målkategori").values))
        self.assertEqual(len(sel["År"]), 1)
        self.assertEqual(q["response"]["format"], "json")

    def test_cell_limit(self):
        import brastat.domstat as d
        old, d.MAX_CELLS = d.MAX_CELLS, 10
        try:
            with self.assertRaises(ValueError):
                build_query(self.t)
        finally:
            d.MAX_CELLS = old


class TestResult(unittest.TestCase):
    def setUp(self):
        self.t = parse_metadata(TABLE, load("domstat_meta_arenden_tr.json"))

    def test_parse_result_long_format(self):
        rows = parse_result(self.t, load("domstat_result_arenden_tr.json"))
        by = {(r["domstol"], r["variabel"], r["ar"]): r for r in rows}
        r = by[("Alla tingsrätter", "Antal inkomna mål", 2025)]
        self.assertEqual(r["varde"], 3174.0)
        self.assertEqual(r["dimension"], "Målkategori")
        self.assertEqual(r["dimensionsvarde"], "Skuldsanering")
        self.assertEqual(r["tabell"], TABLE)
        self.assertEqual(by[("Attunda tingsrätt", "Antal inkomna mål", 2024)]["varde"], 121.0)

    def test_symbols(self):
        res = load("domstat_result_arenden_tr.json")
        res["data"] = res["data"][:3]
        res["data"][0]["values"] = ["-"]
        res["data"][1]["values"] = ["."]
        rows = parse_result(self.t, res)
        self.assertEqual((rows[0]["varde"], rows[0]["symbol"]), (0.0, "-"))
        self.assertEqual((rows[1]["varde"], rows[1]["symbol"]), (None, "."))
        self.assertEqual(rows[2]["symbol"], "")


class TestClientOffline(unittest.TestCase):
    def test_query_and_tree(self):
        dom = DomstatClient(client=FakeHttp())
        rows = dom.query(TABLE, {"Domstol": ["Alla tingsrätter", "Attunda"], "Målkategori": "Skuldsanering"},
                         years="2024-2025")
        self.assertEqual(len(rows), 12)
        url, payload = dom.http.posts[0]
        self.assertTrue(url.endswith("/DOMstat/" + TABLE + ".px"))
        sel = {x["code"]: x["selection"]["values"] for x in payload["query"]}
        self.assertEqual(sel["Målkategori"], ["Debt clearance matters"])
        tree = dom.tree()
        self.assertEqual(tree[0]["path"], "AntalMal/09_Konkurser_TR")
        self.assertEqual(tree[0]["mapp_text"], "Antal mål")


class TestWatchlistConfig(unittest.TestCase):
    def test_config_is_valid(self):
        cfg = json.loads(config_path("watchlist_domstat.json").read_text(encoding="utf-8"))
        names = [s["namn"] for s in cfg["serier"]]
        self.assertEqual(len(names), len(set(names)))
        for s in cfg["serier"]:
            self.assertIn("tabell", s)
            self.assertIsInstance(s.get("urval", {}), dict)


if __name__ == "__main__":
    unittest.main()
