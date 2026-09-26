"""Offline-tester för paketstrukturen: sökvägar, loggning, kommandon och skalen i scripts/."""
import io
import json
import logging
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from brastat import log as blog
from brastat import paths
from brastat.cli import fetch_all, smoke_live

ROOT = Path(__file__).resolve().parent.parent


class TestPaths(unittest.TestCase):
    def test_source_checkout_uses_repo_data(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("BRA_DATA_DIR", None)
            self.assertTrue(paths.is_source_checkout())
            self.assertEqual(paths.data_dir(create=False), ROOT / "data")

    def test_override_and_env(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / "ny"
            self.assertEqual(paths.data_dir(target, create=False), target)
            self.assertFalse(target.exists(), "create=False får inte skapa katalogen")
            with mock.patch.dict(os.environ, {"BRA_DATA_DIR": str(target)}):
                self.assertEqual(paths.data_dir(), target)
            self.assertTrue(target.exists())

    def test_installed_package_uses_user_dir(self):
        with mock.patch.object(paths, "is_source_checkout", return_value=False), \
                mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("BRA_DATA_DIR", None)
            self.assertEqual(paths.data_dir(create=False), paths.user_data_dir())
        self.assertEqual(paths.user_data_dir().name, "brastat")

    def test_bundled_configs(self):
        for name in ("watchlist_aml_fraud.json", "watchlist_domstat.json"):
            cfg = json.loads(paths.config_path(name).read_text(encoding="utf-8"))
            self.assertTrue(cfg["serier"])


class TestLogging(unittest.TestCase):
    def tearDown(self):
        logging.getLogger("brastat").handlers[:] = []

    def test_plain_in_terminal_stamped_otherwise(self):
        for env, expect_stamp in (("0", False), ("1", True)):
            buf = io.StringIO()
            with mock.patch.dict(os.environ, {"BRASTAT_LOG_TIMESTAMPS": env}):
                blog.setup(stream=buf)
            logging.getLogger("brastat.x").info("hej")
            line = buf.getvalue().strip()
            self.assertEqual(line.endswith("brastat.x: hej"), expect_stamp, line)
            if not expect_stamp:
                self.assertEqual(line, "hej")

    def test_levels(self):
        buf = io.StringIO()
        blog.setup(quiet=1, stream=buf)
        logging.getLogger("brastat.x").info("syns inte")
        logging.getLogger("brastat.x").warning("syns")
        self.assertNotIn("syns inte", buf.getvalue())
        self.assertIn("syns", buf.getvalue())


class TestFetchAll(unittest.TestCase):
    def run_main(self, argv):
        calls = []

        def fake_run(cmd):
            calls.append(cmd[2:])  # [sys.executable, "-m", module, *args]
            return subprocess.CompletedProcess(cmd, 0)

        with mock.patch.object(sys, "argv", ["fetch_all", "-q", *argv]), \
                mock.patch("brastat.cli.fetch_all.subprocess.run", side_effect=fake_run), \
                self.assertRaises(SystemExit) as cm:
            fetch_all.main()
        logging.getLogger("brastat").handlers[:] = []
        return cm.exception.code, calls

    def test_full_chain_runs_modules_in_order(self):
        code, calls = self.run_main(["--no-pdf", "--notify"])
        self.assertEqual(code, 0)
        modules = [c[0] for c in calls]
        self.assertEqual(modules[:3], ["brastat.cli.fetch_tables", "brastat.cli.sol_watchlist",
                                       "brastat.cli.domstat_watchlist"])
        self.assertEqual(calls[0][1:], ["--no-pdf"])
        self.assertEqual(calls[-1], ["brastat.cli.check_health", "--notify"])

    def test_only_sol_skip_health(self):
        code, calls = self.run_main(["--only-sol", "--skip-health"])
        self.assertEqual([c[0] for c in calls], ["brastat.cli.sol_watchlist"])


class TestSmoke(unittest.TestCase):
    def test_reports_all_failures(self):
        checks = {"sol": lambda: "ok", "domstat": mock.Mock(side_effect=RuntimeError("nere")), "bra": lambda: "ok"}
        with mock.patch.dict(smoke_live.CHECKS, checks), mock.patch.object(sys, "argv", ["smoke"]), \
                mock.patch.object(blog, "setup_from_args"), self.assertLogs("brastat.smoke_live") as logs, \
                self.assertRaises(SystemExit) as cm:
            smoke_live.main()
        self.assertEqual(cm.exception.code, 1)
        text = "\n".join(logs.output)
        self.assertIn("OK   sol", text)
        self.assertIn("OK   bra", text)
        self.assertIn("FEL  domstat  nere", text)


class TestScriptShims(unittest.TestCase):
    """Varje skal i scripts/ ska peka på en modul med main() och kunna visa --help."""

    def test_shims_import_main(self):
        import importlib
        import re

        shims = sorted((ROOT / "scripts").glob("*.py"))
        self.assertGreaterEqual(len(shims), 15)
        for p in shims:
            with self.subTest(script=p.name):
                m = re.search(r"^from (\S+) import main$", p.read_text(encoding="utf-8"), re.M)
                self.assertIsNotNone(m, "skalet ska importera main från paketet")
                try:
                    mod = importlib.import_module(m.group(1))
                except ImportError as e:  # valfria beroenden (pandas m.fl.) saknas
                    self.skipTest(str(e))
                self.assertTrue(callable(mod.main))

    def test_help_runs_without_install_hack(self):
        env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_health.py"), "--help"],
                           capture_output=True, text=True, encoding="utf-8", env=env, cwd=tempfile.gettempdir())
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Hälsokontroll", r.stdout)


if __name__ == "__main__":
    unittest.main()
