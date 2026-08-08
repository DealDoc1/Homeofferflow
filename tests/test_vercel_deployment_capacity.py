import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "vercel_capacity", ROOT / "scripts" / "check_vercel_deployment_capacity.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class VercelDeploymentCapacityTests(unittest.TestCase):
    def test_counts_only_deployments_inside_rolling_window(self):
        now = 1_000_000
        payload = {
            "deployments": [
                {"created": now},
                {"created": now - 86_399_000},
                {"created": now - 86_401_000},
                {"created": "invalid"},
            ]
        }
        self.assertEqual(
            MODULE._deployment_count(payload, now_ms=now, window_ms=86_400_000), 2
        )

    def test_missing_deployment_list_is_rejected(self):
        with self.assertRaises(ValueError):
            MODULE._deployment_count({}, now_ms=1, window_ms=1)


if __name__ == "__main__":
    unittest.main()
