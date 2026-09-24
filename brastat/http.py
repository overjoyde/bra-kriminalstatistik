"""Minimal HTTP client used by all fetchers (stdlib only, cross-platform).

- Uses urllib with a cookie jar (SOL requires a session cookie).
- TLS trust: prefers the OS trust store via `truststore` (pip install truststore),
  then `certifi`, then Python's default. If verification still fails (e.g. a
  Homebrew/python.org build without CA certs, or a corporate TLS proxy) it falls
  back to the system `curl` binary, which exists on macOS, Linux and Windows 10+.
- statistik.bra.se sends the wrong intermediate certificate (GeoTrust EV RSA CA 2018
  instead of DigiCert EV RSA CA G2). macOS/Windows fetch the right one themselves,
  OpenSSL (Linux, certifi, curl) does not. The correct intermediate is bundled in
  ``digicert_ev_rsa_ca_g2.pem`` and added to the trust store so Linux works too.
- Adds a polite delay between requests.
"""
from __future__ import annotations

import http.cookiejar
import os
import shutil
import ssl
import subprocess
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

USER_AGENT = (
    "Mozilla/5.0 (bra-kriminalstatistik; offentlig statistik, "
    "vidareutnyttjande enligt Brås PSI-villkor; +https://github.com/overjoyde/bra-kriminalstatistik)"
)
DEFAULT_DELAY = 0.3  # seconds between requests – be nice to bra.se
# Intermediate missing from statistik.bra.se's chain (see module docstring). Valid until 2030-07-02.
EXTRA_CA = Path(__file__).with_name("digicert_ev_rsa_ca_g2.pem")


def _ssl_context() -> ssl.SSLContext:
    try:
        import truststore  # type: ignore

        ctx = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    except ImportError:
        ctx = ssl.create_default_context()
        try:
            import certifi  # type: ignore

            ctx.load_verify_locations(certifi.where())
        except ImportError:
            pass
    if EXTRA_CA.exists():
        ctx.load_verify_locations(str(EXTRA_CA))
    return ctx


def _is_ssl_error(e: Exception) -> bool:
    return isinstance(e, ssl.SSLError) or isinstance(getattr(e, "reason", None), ssl.SSLError)


class Client:
    """Small session-aware HTTP client."""

    def __init__(self, delay: float = DEFAULT_DELAY, timeout: float = 60, retries: int = 2):
        self.delay = delay
        self.timeout = timeout
        self.retries = retries
        self.cookies = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookies),
            urllib.request.HTTPSHandler(context=_ssl_context()),
        )
        self.use_curl = os.environ.get("BRASTAT_HTTP", "").lower() == "curl"
        self._curl_jar = os.path.join(tempfile.mkdtemp(prefix="brastat-"), "cookies.txt")

    def _curl(self, url: str, body: bytes | None, referer: str | None) -> bytes:
        exe = shutil.which("curl") or shutil.which("curl.exe")
        if not exe:
            raise RuntimeError("TLS-verifiering misslyckades och curl saknas. Kör: pip install truststore")
        cmd = [exe, "-sSfL", "--retry", str(self.retries), "--max-time", str(int(self.timeout)),
               "-A", USER_AGENT, "-b", self._curl_jar, "-c", self._curl_jar]
        if referer:
            cmd += ["-e", referer]
        if body is not None:
            cmd += ["--data-binary", "@-", "-H", "Content-Type: application/x-www-form-urlencoded"]
        r = subprocess.run(cmd + [url], input=body, capture_output=True)
        if r.returncode != 0:
            raise RuntimeError(f"curl misslyckades ({r.returncode}) för {url}: {r.stderr.decode(errors='replace')}")
        time.sleep(self.delay)
        return r.stdout

    def request(self, url: str, data: dict | None = None, referer: str | None = None) -> bytes:
        body = urllib.parse.urlencode(data).encode("latin-1") if data is not None else None
        headers = {"User-Agent": USER_AGENT, "Accept-Encoding": "identity"}
        if referer:
            headers["Referer"] = referer
        if self.use_curl:
            return self._curl(url, body, referer)
        last: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                req = urllib.request.Request(url, data=body, headers=headers)
                with self.opener.open(req, timeout=self.timeout) as resp:
                    content = resp.read()
                time.sleep(self.delay)
                return content
            except urllib.error.HTTPError as e:
                if e.code < 500:
                    raise
                last = e
            except (urllib.error.URLError, TimeoutError, ConnectionError, ssl.SSLError) as e:
                if _is_ssl_error(e):
                    # Switch permanently to curl for this client (keeps its own cookie jar,
                    # so callers should create the client before starting a SOL session).
                    self.use_curl = True
                    return self._curl(url, body, referer)
                last = e
            time.sleep(1.5 * (attempt + 1))
        raise RuntimeError(f"Kunde inte hämta {url}: {last}")

    def get(self, url: str, referer: str | None = None) -> bytes:
        return self.request(url, None, referer)

    def post(self, url: str, data: dict, referer: str | None = None) -> bytes:
        return self.request(url, data, referer)

    def text(self, url: str, encoding: str = "utf-8", **kw) -> str:
        return self.get(url, **kw).decode(encoding, "replace")
