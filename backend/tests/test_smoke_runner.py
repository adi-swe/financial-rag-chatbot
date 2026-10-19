"""Verify opt-in and prerequisite behavior without contacting Ollama."""

import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch


class SmokeRunnerTests(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).resolve().parents[1] / "scripts/smoke_ollama.py"
        spec = importlib.util.spec_from_file_location("smoke_runner", path)
        self.runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.runner)
        # platform.platform() may call subprocess itself; only application
        # workers should be counted by the process assertions below.
        platform_patch = patch.object(self.runner.platform, "platform", return_value="test-platform")
        platform_patch.start()
        self.addCleanup(platform_patch.stop)

    def test_default_invocation_makes_no_network_calls_or_model_processes(self):
        with patch("sys.argv", ["smoke_ollama.py"]), patch("sys.stdout", io.StringIO()), \
                patch.object(self.runner, "urlopen") as network, \
                patch.object(self.runner.subprocess, "run") as process:
            self.assertEqual(self.runner.main(), 0)
            network.assert_not_called()
            process.assert_not_called()

    def test_connection_failure_returns_nonzero_structured_report(self):
        with patch("sys.argv", ["smoke_ollama.py", "--run"]), \
                patch("sys.stdout", new_callable=io.StringIO) as output, \
                patch.object(self.runner.importlib.metadata, "version", return_value="test"), \
                patch.object(self.runner, "urlopen", side_effect=OSError("synthetic unavailable server")), \
                patch.object(self.runner.subprocess, "run") as process:
            self.assertEqual(self.runner.main(), 1)
            report = json.loads(output.getvalue())
            self.assertEqual(report["status"], "failed")
            self.assertIn("synthetic unavailable server", report["error"])
            process.assert_not_called()

    def test_empty_model_registry_fails_without_starting_workers(self):
        responses = [io.BytesIO(b'{"version":"test-server"}'), io.BytesIO(b'{"models":[]}')]
        with patch("sys.argv", ["smoke_ollama.py", "--run"]), \
                patch("sys.stdout", new_callable=io.StringIO) as output, \
                patch.object(self.runner.importlib.metadata, "version", return_value="test"), \
                patch.object(self.runner, "urlopen", side_effect=responses), \
                patch.object(self.runner.subprocess, "run") as process:
            self.assertEqual(self.runner.main(), 1)
            report = json.loads(output.getvalue())
            self.assertIn("Missing models", report["error"])
            self.assertEqual(report["ollama_server"], "test-server")
            process.assert_not_called()


if __name__ == "__main__":
    unittest.main()
