"""Unit tests for cping with mocked HTTP responses."""

import io
import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Ensure src/ is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from cping import cli


def _make_response(data):
    """Create a mock HTTP response from a dict."""
    body = json.dumps(data).encode("utf-8")
    resp = MagicMock()
    resp.read.return_value = body
    resp.__enter__ = MagicMock(return_value=resp)
    resp.__exit__ = MagicMock(return_value=False)
    return resp


SAMPLE_DATA = {
    "page": {"updated_at": "2026-05-13T09:00:00Z"},
    "status": {"indicator": "none", "description": "All Systems Operational"},
    "components": [
        {"name": "claude.ai", "status": "operational", "showcase": True},
        {"name": "Claude API", "status": "operational", "showcase": True},
        {"name": "Claude Code", "status": "operational", "showcase": True},
    ],
    "incidents": [],
}

DEGRADED_DATA = {
    "page": {"updated_at": "2026-05-13T09:00:00Z"},
    "status": {"indicator": "major", "description": "Partial System Outage"},
    "components": [
        {"name": "claude.ai", "status": "partial_outage", "showcase": True},
        {"name": "Claude API", "status": "operational", "showcase": True},
    ],
    "incidents": [],
}

EMPTY_COMPONENTS_DATA = {
    "page": {"updated_at": "2026-05-13T09:00:00Z"},
    "status": {"indicator": "none"},
    "components": [],
    "incidents": [],
}


class TestFetchStatus(unittest.TestCase):
    """Tests for fetch_status()."""

    @patch("cping.cli.urllib.request.urlopen")
    def test_successful_response(self, mock_urlopen):
        mock_urlopen.return_value = _make_response(SAMPLE_DATA)
        result = cli.fetch_status()
        self.assertEqual(result["status"]["indicator"], "none")
        self.assertEqual(len(result["components"]), 3)

    @patch("cping.cli.urllib.request.urlopen")
    def test_http_error(self, mock_urlopen):
        import urllib.error

        mock_urlopen.side_effect = urllib.error.HTTPError(
            url=cli.STATUS_URL, code=503, msg="Service Unavailable",
            hdrs=None, fp=None,
        )
        with self.assertRaises(SystemExit) as ctx:
            cli.fetch_status()
        self.assertEqual(ctx.exception.code, 1)

    @patch("cping.cli.urllib.request.urlopen")
    def test_url_error(self, mock_urlopen):
        import urllib.error

        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")
        with self.assertRaises(SystemExit) as ctx:
            cli.fetch_status()
        self.assertEqual(ctx.exception.code, 1)

    @patch("cping.cli.urllib.request.urlopen")
    def test_malformed_json(self, mock_urlopen):
        resp = MagicMock()
        resp.read.return_value = b"not json at all"
        resp.__enter__ = MagicMock(return_value=resp)
        resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = resp
        with self.assertRaises(SystemExit) as ctx:
            cli.fetch_status()
        self.assertEqual(ctx.exception.code, 1)


class TestAllOperational(unittest.TestCase):
    """Tests for all_operational()."""

    def test_all_operational(self):
        self.assertTrue(cli.all_operational(SAMPLE_DATA["components"]))

    def test_degraded(self):
        self.assertFalse(cli.all_operational(DEGRADED_DATA["components"]))

    def test_empty_components(self):
        self.assertFalse(cli.all_operational([]))


class TestDisplayStatus(unittest.TestCase):
    """Tests for display_status()."""

    def test_empty_components_returns_false(self):
        captured = io.StringIO()
        with patch("sys.stdout", captured), \
             patch("sys.stderr", io.StringIO()):
            result = cli.display_status(EMPTY_COMPONENTS_DATA, use_color=False)
        self.assertFalse(result)

    def test_successful_display_returns_true(self):
        captured = io.StringIO()
        with patch("sys.stdout", captured):
            result = cli.display_status(SAMPLE_DATA, use_color=False)
        self.assertTrue(result)
        output = captured.getvalue()
        self.assertIn("Claude Service Status", output)
        self.assertIn("claude.ai", output)
        self.assertIn("All Systems Operational", output)

    def test_no_color_output(self):
        captured = io.StringIO()
        with patch("sys.stdout", captured):
            cli.display_status(SAMPLE_DATA, use_color=False)
        output = captured.getvalue()
        self.assertNotIn("\033[", output)

    def test_truncation_with_ellipsis(self):
        long_body = "x" * 300
        data_with_incident = {
            "page": {"updated_at": "2026-05-13T09:00:00Z"},
            "status": {"indicator": "minor"},
            "components": [
                {"name": "API", "status": "operational", "showcase": True},
            ],
            "incidents": [
                {
                    "name": "Test incident",
                    "status": "investigating",
                    "impact": "minor",
                    "incident_updates": [{"body": long_body}],
                }
            ],
        }
        captured = io.StringIO()
        with patch("sys.stdout", captured):
            cli.display_status(data_with_incident, use_color=False)
        output = captured.getvalue()
        self.assertIn("...", output)
        # Should contain exactly 200 chars of body + "..."
        self.assertNotIn("x" * 201, output)


class TestMainExitCodes(unittest.TestCase):
    """Tests for main() exit codes."""

    @patch("cping.cli.fetch_status", return_value=DEGRADED_DATA)
    @patch("sys.stdout", new_callable=io.StringIO)
    def test_degraded_status_exit_code(self, mock_stdout, mock_fetch):
        with patch("sys.argv", ["cping", "--no-color"]):
            with self.assertRaises(SystemExit) as ctx:
                cli.main()
            self.assertEqual(ctx.exception.code, 2)

    @patch("cping.cli.fetch_status", return_value=SAMPLE_DATA)
    @patch("sys.stdout", new_callable=io.StringIO)
    def test_json_operational_exits_0(self, mock_stdout, mock_fetch):
        """--json mode exits 0 when all components are operational."""
        with patch("sys.argv", ["cping", "--json"]):
            with self.assertRaises(SystemExit) as ctx:
                cli.main()
            self.assertEqual(ctx.exception.code, 0)

    @patch("cping.cli.fetch_status", return_value=DEGRADED_DATA)
    @patch("sys.stdout", new_callable=io.StringIO)
    def test_json_exits_0_even_degraded(self, mock_stdout, mock_fetch):
        """--json mode exits 0 even when degraded."""
        with patch("sys.argv", ["cping", "--json"]):
            with self.assertRaises(SystemExit) as ctx:
                cli.main()
            self.assertEqual(ctx.exception.code, 0)


class TestColorEnvironment(unittest.TestCase):
    """Tests for NO_COLOR / FORCE_COLOR env var handling."""

    @patch("cping.cli.fetch_status", return_value=SAMPLE_DATA)
    def test_no_color_env(self, mock_fetch):
        captured = io.StringIO()
        with patch("sys.argv", ["cping"]), \
             patch("sys.stdout", captured), \
             patch.dict(os.environ, {"NO_COLOR": "1"}, clear=False):
            try:
                cli.main()
            except SystemExit:
                pass
        output = captured.getvalue()
        self.assertNotIn("\033[", output)

    @patch("cping.cli.fetch_status", return_value=SAMPLE_DATA)
    def test_force_color_env(self, mock_fetch):
        captured = io.StringIO()
        captured.isatty = lambda: False
        env = os.environ.copy()
        env.pop("NO_COLOR", None)
        env["FORCE_COLOR"] = "1"
        with patch("sys.argv", ["cping"]), \
             patch("sys.stdout", captured), \
             patch.dict(os.environ, env, clear=True):
            try:
                cli.main()
            except SystemExit:
                pass
        output = captured.getvalue()
        self.assertIn("\033[", output)


if __name__ == "__main__":
    unittest.main()
