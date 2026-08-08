import importlib.util
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "release_base_ref", ROOT / "scripts" / "release_base_ref.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


class ReleaseBaseRefTests(unittest.TestCase):
    def test_resolves_prior_production_marker_and_skips_current_marker(self):
        completed = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=(
                "current\x00[deploy-production] candidate marker\n"
                "verified\x00[deploy-production] verified release\n"
                "older\x00older commit\n"
            ),
        )
        with patch.object(MODULE.subprocess, "run", return_value=completed):
            self.assertEqual(MODULE.resolve_base_ref(), "current")

    def test_fails_closed_without_prior_marker(self):
        completed = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="abc\x00ordinary commit\n"
        )
        with patch.object(MODULE.subprocess, "run", return_value=completed):
            with self.assertRaises(RuntimeError):
                MODULE.resolve_base_ref()


if __name__ == "__main__":
    unittest.main()
