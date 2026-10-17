import copy
import importlib.util
from pathlib import Path
import subprocess
import unittest
from unittest.mock import AsyncMock, patch

from lib.partner_operations import annotate_partner_operations, is_paid_partner

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('partner_operations_admin', ROOT / 'api/admin-dashboard.py')
admin = importlib.util.module_from_spec(spec)
spec.loader.exec_module(admin)


class PartnerOperationsTests(unittest.TestCase):
    def test_beta_never_counts_as_paid_even_with_a_legacy_paid_flag(self):
        self.assertFalse(is_paid_partner({'partner_program': 'beta', 'payment_status': 'paid'}))
        self.assertFalse(is_paid_partner(None))
        self.assertFalse(is_paid_partner({'partner_program': 'unknown', 'payment_status': 'paid'}))
        self.assertFalse(is_paid_partner({'payment_status': 'not_started'}))
        self.assertTrue(is_paid_partner({'payment_status': 'paid'}))
        self.assertTrue(is_paid_partner({'partner_program': 'commercial', 'payment_status': ' PAID '}))

    def test_read_model_uses_the_central_program_not_zero_fee_or_a_placement_claim(self):
        leads = [{'id': 'beta', 'partner_program': 'beta'}, {'id': 'paid', 'payment_status': 'paid'}]
        placements = [{'source_lead_id': 'beta', 'is_active': True, 'monthly_fee': 0},
                      {'source_lead_id': 'paid', 'is_active': False, 'monthly_fee': 0},
                      {'source_lead_id': 'missing', 'is_active': True, 'partner_program': 'beta', 'monthly_fee': 0}]
        before = copy.deepcopy((leads, placements))
        rows, cards = annotate_partner_operations(leads, placements)
        self.assertEqual([row['has_active_placement'] for row in rows], [True, False])
        self.assertEqual([row['partner_program'] for row in cards], ['beta', 'commercial', 'unknown'])
        self.assertEqual((leads, placements), before)

    def dashboard(self, leads, placements, authorized=True):
        datasets = {'hof_partner_leads': leads, 'hof_partner_placements': placements}

        async def read_datasets(*queries):
            return [copy.deepcopy(datasets.get(query[0].split('?')[0], [])) for query in queries]

        request = object.__new__(admin.handler)
        request.path = '/api/admin-dashboard'
        request.headers = {'authorization': 'Bearer fictional-qa-session'}
        with patch.object(admin, 'SUPABASE_URL', 'https://example.supabase.co'), \
             patch.object(admin, 'SUPABASE_SERVICE_ROLE_KEY', 'fixture-only'), \
             patch.object(admin, '_verified_user', AsyncMock(return_value={'id': 'qa-operator'})), \
             patch.object(admin, '_is_platform_admin', AsyncMock(return_value=authorized)), \
             patch.object(admin, '_get_dashboard_datasets', side_effect=read_datasets) as reads, \
             patch.object(admin, '_get_optional', AsyncMock(return_value=[])), \
             patch.object(admin.httpx, 'Client', side_effect=AssertionError('Unexpected external call')), \
             patch.object(admin, '_json') as response:
            request.do_GET()
        return response.call_args.args[1:], reads.call_count

    def test_actual_admin_response_separates_two_beta_placements_from_paid_activation(self):
        leads = [
            {'id': 'beta1', 'company_name': 'Roof Company', 'partner_program': 'beta', 'payment_status': 'not_started', 'onboarding_status': 'complete', 'created_at': '2026-01-01T00:00:00Z'},
            {'id': 'beta2', 'company_name': 'Insurance Company', 'partner_program': 'beta', 'payment_status': 'paid', 'onboarding_status': 'complete', 'partner_agreement_status': 'signed'},
            {'id': 'paid1', 'company_name': 'Paid Company', 'payment_status': 'paid', 'created_at': '2026-10-01T00:00:00Z'},
            {'id': 'paid2', 'company_name': 'Pending Company', 'payment_status': 'paid', 'created_at': '2026-10-01T00:00:00Z'},
        ]
        placements = [
            {'id': 'p1', 'source_lead_id': 'beta1', 'is_active': True, 'monthly_fee': 0, 'activated_at': '2026-10-03T00:00:00Z'},
            {'id': 'p2', 'source_lead_id': 'beta2', 'is_active': True, 'monthly_fee': 0},
            {'id': 'p3', 'source_lead_id': 'paid1', 'is_active': True, 'monthly_fee': 149, 'activated_at': '2026-10-03T00:00:00Z'},
        ]
        (status, result), reads = self.dashboard(leads, placements)
        self.assertEqual(status, 200, result)
        self.assertEqual(reads, 2)
        metrics = result['metrics']
        self.assertEqual(metrics['paidPartnerLeadCount'], 2)
        self.assertEqual(metrics['partnerActivationRate'], 50)
        self.assertEqual(metrics['partnerActivationAvgDays'], 2)
        self.assertEqual(metrics['partnerOnboardingCompletedCount'], 0)
        self.assertEqual(metrics['paidPartnerAgreementConfirmedCount'], 0)
        self.assertEqual([row['id'] for row in result['paidPartnerActivationQueue']], ['paid2'])
        self.assertEqual(result['partnerLeads'][0]['activation_readiness']['code'], 'beta_live')
        self.assertEqual(result['partnerPlacements'][0]['partner_program'], 'beta')

    def test_actual_admin_response_retains_the_existing_authorization_boundary(self):
        (status, result), reads = self.dashboard([], [], authorized=False)
        self.assertEqual(status, 403)
        self.assertEqual(reads, 0)
        self.assertNotIn('partnerPlacements', result)

    def test_actual_javascript_lifecycle_and_contact_actions(self):
        result = subprocess.run(['node', '--test', str(ROOT / 'tests/partner_operations.runtime.cjs')], capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
