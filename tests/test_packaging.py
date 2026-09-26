"""Håller pyproject.toml, requirements.txt och requirements.lock i synk."""
import re
import unittest
from pathlib import Path

try:
    import tomllib
except ImportError:  # Python 3.10
    tomllib = None

ROOT = Path(__file__).resolve().parent.parent


def reqs(path: Path) -> dict[str, str]:
    """namn -> versionsvillkor, utan kommentarer och miljömarkörer."""
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].split(";", 1)[0].strip()
        if line:
            m = re.match(r"([A-Za-z0-9_.-]+)\s*(.*)", line)
            out[m.group(1).lower().replace("_", "-")] = m.group(2).replace(" ", "")
    return out


class TestPackaging(unittest.TestCase):
    @unittest.skipIf(tomllib is None, "tomllib kräver Python 3.11+")
    def test_pyproject_matches_requirements(self):
        project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
        declared = project["dependencies"] + project["optional-dependencies"]["analysis"]
        from_pyproject = {}
        for d in declared:
            m = re.match(r"([A-Za-z0-9_.-]+)\s*(.*)", d)
            from_pyproject[m.group(1).lower()] = m.group(2).replace(" ", "")
        self.assertEqual(from_pyproject, reqs(ROOT / "requirements.txt"))

    def test_lock_pins_every_direct_dependency(self):
        lock = (ROOT / "requirements.lock").read_text(encoding="utf-8")
        pinned = {m.group(1).lower() for m in re.finditer(r"^([A-Za-z0-9_.-]+)==", lock, flags=re.M)}
        missing = set(reqs(ROOT / "requirements.txt")) - pinned
        self.assertFalse(missing, f"saknas i requirements.lock: {missing} – kör uv pip compile (se requirements.txt)")

    def test_every_direct_dependency_is_bounded(self):
        for name, spec in reqs(ROOT / "requirements.txt").items():
            with self.subTest(name=name):
                self.assertIn(">=", spec)
                self.assertIn("<", spec.replace("<=", "<"))

    def test_changelog_matches_version(self):
        import brastat

        top = re.search(r"^## \[(\d+\.\d+\.\d+)\]", (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"), re.M)
        self.assertIsNotNone(top, "CHANGELOG.md saknar versionsrubrik")
        self.assertEqual(top.group(1), brastat.__version__, "uppdatera CHANGELOG.md eller brastat.__version__")


if __name__ == "__main__":
    unittest.main()
