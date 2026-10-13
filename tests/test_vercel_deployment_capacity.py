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
        now = 1_791_924_266_000
        payload = {
            "deployments": [
                {"created": now},
                {"created": now - 86_399_000},
                {"created": now - 86_401_000},
                {"created": now + 1},
            ]
        }
        self.assertEqual(
            MODULE._deployment_count(payload, now_ms=now, window_ms=86_400_000), 2
        )

    def test_missing_deployment_list_is_rejected(self):
        with self.assertRaises(ValueError):
            MODULE._deployment_count({}, now_ms=1, window_ms=1)

    def test_bad_timestamps_fail_closed_instead_of_becoming_zero_usage(self):
        for row in ({}, {'created':'invalid'}, {'created':True}, {'created':float('nan')}, {'created':float('inf')}, None):
            with self.subTest(row=row), self.assertRaises(ValueError):
                MODULE._deployment_count({'deployments':[row]},now_ms=1000,window_ms=500)

    def test_both_time_boundaries_are_inclusive_and_created_at_is_supported(self):
        self.assertEqual(MODULE._deployment_count({'deployments':[{'created':500},{'createdAt':1000},{'created':499},{'created':1001}]},now_ms=1000,window_ms=500),2)

    def _fetch(self, pages, stop_at=100):
        import io
        from urllib.parse import parse_qs, urlparse
        calls=[]
        def response(request, timeout):
            calls.append(parse_qs(urlparse(request.full_url).query))
            self.assertIn('/v7/deployments?',request.full_url)
            self.assertNotIn('fixture-token',request.full_url)
            return io.StringIO(json.dumps(pages[len(calls)-1]))
        with patch.object(MODULE,'urlopen',side_effect=response):
            count=MODULE.fetch_deployment_count(token='fixture-token',project_id='project',team_id='team',now_ms=100_000,window_seconds=10,stop_at=stop_at)
        return count,calls

    def test_request_uses_current_since_until_filters_not_deprecated_from(self):
        count,calls=self._fetch([{'deployments':[{'uid':'a','created':95_000}], 'pagination':{'count':1}}])
        self.assertEqual(count,1)
        self.assertEqual(calls[0]['since'],['89999'])
        self.assertEqual(calls[0]['until'],['100001'])
        self.assertNotIn('from',calls[0])
        self.assertEqual(calls[0]['projectId'],['project'])
        self.assertEqual(calls[0]['teamId'],['team'])

    def test_pagination_counts_all_pages_and_preserves_lower_time_bound(self):
        count,calls=self._fetch([
            {'deployments':[{'id':'a','created':98_000}], 'pagination':{'count':1,'next':97_000}},
            {'deployments':[{'id':'b','created':96_000}], 'pagination':{'count':1}},
        ])
        self.assertEqual(count,2)
        self.assertEqual(calls[1]['until'],['97000'])
        self.assertEqual(calls[1]['since'],calls[0]['since'])

    def test_threshold_stops_further_api_reads_without_understating_capacity(self):
        count,calls=self._fetch([{'deployments':[{'id':str(i),'created':95_000} for i in range(100)]}],stop_at=100)
        self.assertEqual(count,100)
        self.assertEqual(len(calls),1)

    def test_malformed_or_repeated_pagination_is_not_accepted_as_safe(self):
        for pagination in ({'count':1,'next':100001},{'count':1,'next':True},{'count':1,'next':'invalid'},{'count':1,'next':float('nan')},{'count':2},None):
            with self.subTest(pagination=pagination), self.assertRaises(ValueError):
                self._fetch([{'deployments':[{'id':'a','created':95000}], 'pagination':pagination}])
        with self.assertRaises(ValueError):
            self._fetch([{'deployments':[{'id':'a','created':98000}],'pagination':{'count':1,'next':97000}},
                         {'deployments':[{'id':'a','created':96000}],'pagination':{'count':1}}])

    def test_real_minimized_response_reproduces_nine_recent_deployments(self):
        import io
        snapshot=json.loads((ROOT/'tests/fixtures/vercel_deployment_window_2026_10_13.json').read_text())
        with patch.object(MODULE,'urlopen',return_value=io.StringIO(json.dumps(snapshot))):
            count=MODULE.fetch_deployment_count(token='fixture-token',project_id='project',team_id='team',
                                                now_ms=snapshot['now_ms'],window_seconds=snapshot['window_seconds'])
        self.assertEqual(count,9)

    def test_malformed_capacity_does_not_reach_billing_or_allow_a_release(self):
        import io
        from contextlib import redirect_stderr
        with patch.object(MODULE.sys,'argv',['capacity']), patch.dict(MODULE.os.environ,{'VERCEL_TOKEN':'fixture'}), \
             patch.object(MODULE,'fetch_deployment_count',side_effect=ValueError('malformed response')), \
             patch.object(MODULE,'fetch_billing_usage') as billing, redirect_stderr(io.StringIO()):
            self.assertEqual(MODULE.main(),2)
        billing.assert_not_called()

    def test_read_only_workflow_cannot_build_deploy_or_pull_app_environment(self):
        workflow=(ROOT/'.github/workflows/capacity-check.yml').read_text()
        self.assertIn("github.ref == 'refs/heads/main'",workflow)
        self.assertIn('contents: read',workflow)
        self.assertIn('persist-credentials: false',workflow)
        self.assertIn('environment: production',workflow)
        self.assertIn('python scripts/check_vercel_deployment_capacity.py',workflow)
        for mutation in ('vercel deploy','vercel build','vercel pull','vercel env','SUPABASE_SECRET','SIGNWELL'):
            self.assertNotIn(mutation,workflow)

    def test_deprecated_filter_failure_response_cannot_silently_count_zero(self):
        with self.assertRaisesRegex(ValueError,'ignored'):
            self._fetch([{'deployments':[{'id':'old','created':80000}], 'pagination':{}}])

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
