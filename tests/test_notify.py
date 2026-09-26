"""Offline-tester för aviseringar (brastat.notify) – inga riktiga utskick görs."""
import os
import subprocess
import unittest
from unittest import mock

from brastat import notify


class TestNotify(unittest.TestCase):
    def env(self, **kw):
        patcher = mock.patch.dict(os.environ, kw, clear=False)
        patcher.start()
        self.addCleanup(patcher.stop)
        for k in ("BRASTAT_NOTIFY_WEBHOOK", "BRASTAT_NOTIFY_EMAIL", "BRASTAT_SMTP_HOST", "BRASTAT_SMTP_PORT",
                  "BRASTAT_SMTP_USER", "BRASTAT_SMTP_PASSWORD"):
            if k not in kw:
                os.environ.pop(k, None)

    def test_nothing_configured(self):
        self.env(BRASTAT_NOTIFY_DESKTOP="0")
        self.assertEqual(notify.notify("t", "m"), {})

    def test_webhook_payload(self):
        self.env(BRASTAT_NOTIFY_DESKTOP="0", BRASTAT_NOTIFY_WEBHOOK="https://example.invalid/hook")
        with mock.patch("brastat.http.Client.post_json", return_value=b"ok") as post:
            self.assertEqual(notify.notify("Rubrik", "Text"), {"webhook": True})
        url, payload = post.call_args.args
        self.assertEqual(url, "https://example.invalid/hook")
        self.assertEqual(payload, {"text": "*Rubrik*\nText"})

    def test_failure_is_logged_not_raised(self):
        self.env(BRASTAT_NOTIFY_DESKTOP="0", BRASTAT_NOTIFY_WEBHOOK="https://example.invalid/hook")
        with mock.patch("brastat.http.Client.post_json", side_effect=RuntimeError("nere")), \
                self.assertLogs("brastat.notify", "WARNING") as cm:
            self.assertEqual(notify.notify("t", "m"), {"webhook": False})
        self.assertIn("nere", cm.output[0])

    def test_email_starttls_and_login(self):
        self.env(BRASTAT_NOTIFY_DESKTOP="0", BRASTAT_NOTIFY_EMAIL="a@example.invalid", BRASTAT_SMTP_HOST="smtp.x",
                 BRASTAT_SMTP_USER="u", BRASTAT_SMTP_PASSWORD="p")
        with mock.patch("smtplib.SMTP") as smtp:
            self.assertEqual(notify.notify("Rubrik", "Text"), {"email": True})
        smtp.assert_called_once_with("smtp.x", 587, timeout=30)
        s = smtp.return_value.__enter__.return_value
        s.starttls.assert_called_once()
        s.login.assert_called_once_with("u", "p")
        msg = s.send_message.call_args.args[0]
        self.assertEqual((msg["To"], msg["Subject"], msg["From"]), ("a@example.invalid", "Rubrik", "u"))

    def test_email_without_host(self):
        self.env(BRASTAT_NOTIFY_DESKTOP="0", BRASTAT_NOTIFY_EMAIL="a@example.invalid")
        with self.assertLogs("brastat.notify", "WARNING"):
            self.assertEqual(notify.notify("t", "m"), {"email": False})

    def test_desktop_commands(self):
        self.env(BRASTAT_NOTIFY_DESKTOP="1")
        ok = subprocess.CompletedProcess([], 0)
        with mock.patch("brastat.notify.subprocess.run", return_value=ok) as run, \
                mock.patch("brastat.notify.shutil.which", return_value="/usr/bin/x"):
            with mock.patch.object(notify.sys, "platform", "darwin"):
                self.assertEqual(notify.notify('Ti"tel', "m"), {"desktop": True})
                self.assertEqual(run.call_args.args[0][0], "osascript")
                self.assertIn('Ti\\"tel', run.call_args.args[0][2])
            with mock.patch.object(notify.sys, "platform", "linux"), mock.patch.object(notify.os, "name", "posix"):
                notify.notify("t", "m")
                self.assertEqual(run.call_args.args[0][:3], ["notify-send", "-u", "critical"])


if __name__ == "__main__":
    unittest.main()
