"""Aviseringar när den schemalagda körningen hittar fel (används av ``check_health.py --notify``).

Kanaler (alla som är konfigurerade används; inga hemligheter lagras i repot):

- **Skrivbord** – macOS (``osascript``), Linux (``notify-send``) och Windows (ballongtips via PowerShell).
  Stängs av med ``BRASTAT_NOTIFY_DESKTOP=0``. Kräver en inloggad skrivbordssession.
- **Webhook** – ``BRASTAT_NOTIFY_WEBHOOK=<url>``. Skickar JSON ``{"text": "..."}``, vilket fungerar med
  t.ex. Slack incoming webhooks, Mattermost och Discord (``/slack``-ändpunkten).
- **E-post** – ``BRASTAT_NOTIFY_EMAIL=<mottagare>`` och ``BRASTAT_SMTP_HOST``; valfritt
  ``BRASTAT_SMTP_PORT`` (587), ``BRASTAT_SMTP_USER``, ``BRASTAT_SMTP_PASSWORD`` och ``BRASTAT_SMTP_FROM``.
  STARTTLS används när porten inte är 465 (då SMTP över TLS).

Ett misslyckat utskick loggas men stoppar aldrig körningen.
"""

from __future__ import annotations

import logging
import os
import shutil
import smtplib
import subprocess
import sys
from email.message import EmailMessage

log = logging.getLogger(__name__)

TITLE = "bra-kriminalstatistik"


def _desktop(title: str, text: str) -> bool:
    short = text if len(text) <= 240 else text[:237] + "…"
    if sys.platform == "darwin" and shutil.which("osascript"):
        esc = lambda s: s.replace("\\", "\\\\").replace('"', '\\"')  # noqa: E731
        cmd = ["osascript", "-e", f'display notification "{esc(short)}" with title "{esc(title)}"']
    elif os.name == "nt" and shutil.which("powershell"):
        ps = (
            "Add-Type -AssemblyName System.Windows.Forms; $n = New-Object System.Windows.Forms.NotifyIcon; "
            "$n.Icon = [System.Drawing.SystemIcons]::Warning; $n.Visible = $true; "
            "$n.ShowBalloonTip(10000, $env:BRASTAT_T, $env:BRASTAT_M, 'Warning'); Start-Sleep -Seconds 10; "
            "$n.Dispose()"
        )
        cmd = ["powershell", "-NoProfile", "-Command", ps]
        os.environ["BRASTAT_T"], os.environ["BRASTAT_M"] = title, short
    elif shutil.which("notify-send"):
        cmd = ["notify-send", "-u", "critical", title, short]
    else:
        return False
    r = subprocess.run(cmd, capture_output=True, timeout=30)
    return r.returncode == 0


def _webhook(url: str, title: str, text: str) -> bool:
    from .http import Client

    Client(delay=0, retries=1, timeout=20).post_json(url, {"text": f"*{title}*\n{text}"})
    return True


def _email(to: str, title: str, text: str) -> bool:
    host = os.environ.get("BRASTAT_SMTP_HOST")
    if not host:
        log.warning("BRASTAT_NOTIFY_EMAIL är satt men BRASTAT_SMTP_HOST saknas – hoppar över e-post")
        return False
    port = int(os.environ.get("BRASTAT_SMTP_PORT") or 587)
    user, password = os.environ.get("BRASTAT_SMTP_USER"), os.environ.get("BRASTAT_SMTP_PASSWORD")
    msg = EmailMessage()
    msg["Subject"], msg["To"] = title, to
    msg["From"] = os.environ.get("BRASTAT_SMTP_FROM") or user or to
    msg.set_content(text)
    smtp_cls = smtplib.SMTP_SSL if port == 465 else smtplib.SMTP
    with smtp_cls(host, port, timeout=30) as s:
        if port != 465:
            s.starttls()
        if user and password:
            s.login(user, password)
        s.send_message(msg)
    return True


def notify(title: str, text: str) -> dict[str, bool]:
    """Skicka till alla konfigurerade kanaler. Returnerar kanal -> lyckades."""
    sent: dict[str, bool] = {}
    channels = []
    if os.environ.get("BRASTAT_NOTIFY_DESKTOP", "1") != "0":
        channels.append(("desktop", lambda: _desktop(title, text)))
    if url := os.environ.get("BRASTAT_NOTIFY_WEBHOOK"):
        channels.append(("webhook", lambda: _webhook(url, title, text)))
    if to := os.environ.get("BRASTAT_NOTIFY_EMAIL"):
        channels.append(("email", lambda: _email(to, title, text)))
    for name, send in channels:
        try:
            sent[name] = bool(send())
        except Exception as e:  # noqa: BLE001 – en avisering får aldrig stoppa körningen
            log.warning("avisering via %s misslyckades: %s", name, e)
            sent[name] = False
    return sent
