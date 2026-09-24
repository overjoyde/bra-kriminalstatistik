"""Offline-test för TLS-kontexten (kör: python -m unittest discover -s tests)."""
import ssl
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from brastat.http import EXTRA_CA, _ssl_context  # noqa: E402


class TestSslContext(unittest.TestCase):
    def test_bundled_intermediate_loads(self):
        self.assertTrue(EXTRA_CA.exists())
        ctx = ssl.create_default_context(cafile=str(EXTRA_CA))
        names = [dict(x[0] for x in c["subject"]).get("commonName") for c in ctx.get_ca_certs()]
        self.assertIn("DigiCert EV RSA CA G2", names)

    def test_context_builds(self):
        self.assertIsInstance(_ssl_context(), ssl.SSLContext)


if __name__ == "__main__":
    unittest.main()
