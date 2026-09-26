"""Offline-test för färgteman i brastat/theme.py."""
import unittest

from brastat import theme

try:
    import matplotlib
    matplotlib.use("Agg")
except ImportError:  # matplotlib saknas
    matplotlib = None


class TestPalettes(unittest.TestCase):
    def test_same_number_of_series(self):
        self.assertEqual(len(theme.PALETTES["light"]), len(theme.PALETTES["dark"]))

    def test_unknown_theme(self):
        with self.assertRaises(ValueError):
            theme.rc("sepia")


@unittest.skipIf(matplotlib is None, "matplotlib saknas")
class TestApply(unittest.TestCase):
    def tearDown(self):
        matplotlib.rcdefaults()

    def test_dark_sets_background_and_series(self):
        theme.apply("dark")
        rc = matplotlib.rcParams
        self.assertEqual(rc["axes.facecolor"], theme.COLORS["dark"]["bg"])
        self.assertEqual(rc["axes.prop_cycle"].by_key()["color"], theme.PALETTES["dark"])

    def test_light_restores(self):
        theme.apply("dark")
        theme.apply("light")
        self.assertEqual(matplotlib.rcParams["axes.facecolor"], "white")

    def test_backend_unchanged(self):
        before = matplotlib.get_backend()
        theme.apply("dark")
        self.assertEqual(matplotlib.get_backend(), before)


if __name__ == "__main__":
    unittest.main()
