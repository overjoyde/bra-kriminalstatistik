"""Offline-test för ordningen på månadsfiler i brastat.analysis.parse_bra."""
import unittest

try:
    from brastat.analysis import parse_bra as pb
except ImportError:  # pandas saknas
    pb = None


@unittest.skipIf(pb is None, "pandas saknas")
class TestFileOrder(unittest.TestCase):
    def test_file_period(self):
        self.assertEqual(pb.file_period("x/P4LaAug-2026.xlsx"), (2026, 8))
        self.assertEqual(pb.file_period("P4Rn06Dec-2025.xlsx"), (2025, 12))
        self.assertEqual(pb.file_period("P1xLa-2020.xls"), (2020, 12))

    def test_newest_publication_sorts_last(self):
        files = ["P4LaAug-2026.xlsx", "P4LaDec-2026.xlsx", "P4LaSep-2026.xlsx", "P4LaDec-2025.xlsx"]
        self.assertEqual(sorted(files, key=pb.file_period),
                         ["P4LaDec-2025.xlsx", "P4LaAug-2026.xlsx", "P4LaSep-2026.xlsx", "P4LaDec-2026.xlsx"])


if __name__ == "__main__":
    unittest.main()
