"""Offline-tester för TLS-kontexten och curl-reserven (kör: python -m unittest discover -s tests)."""
import os
import ssl
import subprocess
import unittest
from unittest import mock

from brastat.http import EXTRA_CA, Client, _ssl_context


class TestSslContext(unittest.TestCase):
    def test_bundled_intermediate_loads(self):
        self.assertTrue(EXTRA_CA.exists())
        ctx = ssl.create_default_context(cafile=str(EXTRA_CA))
        names = [dict(x[0] for x in c["subject"]).get("commonName") for c in ctx.get_ca_certs()]
        self.assertIn("DigiCert EV RSA CA G2", names)

    def test_context_builds(self):
        self.assertIsInstance(_ssl_context(), ssl.SSLContext)


class TestCurlFallback(unittest.TestCase):
    """curl-anropet ska läsa kroppen från en temporär fil – aldrig från stdin."""

    def setUp(self):
        self.client = Client(delay=0)
        self.client.use_curl = True
        self.seen = {}

        def fake_run(cmd, **kw):
            self.seen["cmd"], self.seen["kw"] = cmd, kw
            arg = cmd[cmd.index("--data-binary") + 1] if "--data-binary" in cmd else None
            if arg:
                self.seen["path"] = arg[1:]
                with open(arg[1:], "rb") as f:
                    self.seen["body"] = f.read()
            return subprocess.CompletedProcess(cmd, 0, stdout=b"svar", stderr=b"")

        patcher = mock.patch("brastat.http.subprocess.run", side_effect=fake_run)
        patcher.start()
        self.addCleanup(patcher.stop)
        which = mock.patch("brastat.http.shutil.which", return_value="/usr/bin/curl")
        which.start()
        self.addCleanup(which.stop)

    def test_post_body_via_temp_file(self):
        out = self.client.post_json("https://example.invalid/api", {"år": 2025})
        self.assertEqual(out, b"svar")
        self.assertEqual(self.seen["body"], '{"år": 2025}'.encode())
        self.assertNotIn("input", self.seen["kw"])
        self.assertIs(self.seen["kw"]["stdin"], subprocess.DEVNULL)
        self.assertIn("Content-Type: application/json", self.seen["cmd"])
        self.assertFalse(os.path.exists(self.seen["path"]), "den temporära filen ska tas bort")

    def test_get_has_no_body(self):
        self.client.get("https://example.invalid/")
        self.assertNotIn("--data-binary", self.seen["cmd"])
        self.assertIs(self.seen["kw"]["stdin"], subprocess.DEVNULL)

    def test_temp_file_removed_on_failure(self):
        with mock.patch("brastat.http.subprocess.run", side_effect=OSError("boom")):
            with self.assertRaises(OSError):
                self.client.post("https://example.invalid/", {"a": "b"})
        self.assertEqual([f for f in os.listdir(self.client._tmpdir) if f.startswith("body-")], [])


if __name__ == "__main__":
    unittest.main()
