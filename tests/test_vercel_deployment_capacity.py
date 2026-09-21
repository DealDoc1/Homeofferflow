import importlib.util
import json
from pathlib import Path
from unittest.mock import patch
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "vercel_capacity", ROOT / "scripts" / "check_vercel_deployment_capacity.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class VercelDeploymentCapacityTests(unittest.TestCase):
    def test_default_limit_is_the_conservative_release_safety_threshold(self):
        self.assertEqual(MODULE.DEFAULT_LIMIT, 100)

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

    def test_infrastructure_cost_excludes_fixed_plan_charge(self):
        payload = {
            "services": [
                {"name": "Pro", "effectiveCost": 20.0},
                {"name": "Build CPU Minutes", "effectiveCost": 12.5},
                {"name": "Web Analytics Events", "effectiveCost": 0.25},
            ]
        }
        self.assertEqual(MODULE._infrastructure_cost(payload), 12.75)

    def test_usage_without_services_is_rejected(self):
        with self.assertRaises(ValueError):
            MODULE._infrastructure_cost({})

    def test_non_numeric_usage_cost_is_rejected(self):
        with self.assertRaises(ValueError):
            MODULE._infrastructure_cost(
                {"services": [{"name": "Build CPU Minutes", "effectiveCost": "1"}]}
            )

    def test_cycle_dates_use_configured_billing_day(self):
        start, end = MODULE._billing_cycle_dates(
            now=MODULE.datetime(2026, 9, 21, 12, tzinfo=MODULE.UTC),
            billing_cycle_day=22,
        )
        self.assertEqual(start, "2026-08-22")
        self.assertEqual(end, "2026-09-21")

    def test_cycle_dates_roll_over_on_billing_day(self):
        start, end = MODULE._billing_cycle_dates(
            now=MODULE.datetime(2026, 9, 22, 12, tzinfo=MODULE.UTC),
            billing_cycle_day=22,
        )
        self.assertEqual(start, "2026-09-22")
        self.assertEqual(end, "2026-10-21")

    @patch.object(MODULE.subprocess, "run")
    def test_usage_cli_is_machine_readable_and_scoped(self, run):
        run.return_value.stdout = json.dumps(
            {
                "services": [
                    {"name": "Build CPU Minutes", "effectiveCost": 4.0}
                ]
            }
        )
        payload = MODULE.fetch_billing_usage(
            token="secret",
            team_slug="team-slug",
            cycle_start="2026-09-22",
            cycle_end="2026-10-21",
        )
        self.assertEqual(payload["services"][0]["effectiveCost"], 4.0)
        command = run.call_args.args[0]
        self.assertIn("--format", command)
        self.assertIn("json", command)
        self.assertIn("--scope", command)
        self.assertIn("team-slug", command)
        self.assertNotIn("secret", command)
        self.assertEqual(run.call_args.kwargs["env"]["VERCEL_TOKEN"], "secret")

    def test_spend_guard_blocks_before_credit_is_exhausted(self):
        self.assertFalse(
            MODULE._has_safe_credit_headroom(
                infrastructure_cost=18.0,
                monthly_credit=20.0,
                reserve=3.0,
            )
        )

    def test_spend_guard_allows_release_with_reserve_remaining(self):
        self.assertTrue(
            MODULE._has_safe_credit_headroom(
                infrastructure_cost=16.99,
                monthly_credit=20.0,
                reserve=3.0,
            )
        )


if __name__ == "__main__":
    unittest.main()
