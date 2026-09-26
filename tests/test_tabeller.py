"""Offline-test för cachning i brastat.tabeller (kör: python -m unittest discover -s tests)."""
import tempfile
import unittest
from pathlib import Path

from brastat.tabeller import TableFetcher

OLD = "https://bra.se/download/18.1/1000/P4LaDec-2025.xlsx"
NEW = "https://bra.se/download/18.2/2000/P4LaDec-2025.xlsx"


class FakeHttp:
    def __init__(self):
        self.calls = []

    def get(self, url, referer=None):
        self.calls.append(url)
        return url.encode()


class TestCache(unittest.TestCase):
    def run_save(self, out: Path, url: str) -> FakeHttp:
        http = FakeHttp()
        f = TableFetcher(out, client=http)
        f.save(url, out / "raw" / "tidsserie" / "P4LaDec-2025.xlsx", "anmalda")
        f.write_manifest()
        return http

    def test_refetch_when_url_changes(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            dest = out / "raw" / "tidsserie" / "P4LaDec-2025.xlsx"
            self.assertEqual(self.run_save(out, OLD).calls, [OLD])
            self.assertEqual(self.run_save(out, OLD).calls, [])      # oförändrad länk -> cache
            self.assertEqual(self.run_save(out, NEW).calls, [NEW])   # ny version -> hämta om
            self.assertEqual(dest.read_bytes(), NEW.encode())
            self.assertEqual(self.run_save(out, NEW).calls, [])


if __name__ == "__main__":
    unittest.main()
