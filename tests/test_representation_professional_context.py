"""Library storage ownership must never determine the agent's identity."""
import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from tests.test_txr_signing_request_path import MODULE

USER = {'id': 'agent-owner', 'email': 'agent@example.test'}
PROFILE = {'agent_name': 'Own Agent', 'license_number': '1111111',
           'agent_email': 'profile@example.test', 'brokerage_name': 'Own Brokerage',
           'brokerage_license': '2222222'}


class RepresentationProfessionalContextTests(unittest.TestCase):
    def test_independent_agent_uses_own_profile_without_a_seat(self):
        query = AsyncMock(side_effect=[[PROFILE], []])
        with patch.object(MODULE, '_get', query):
            result = asyncio.run(MODULE._representation_professional_context(USER))
        self.assertEqual(result['profile'], PROFILE)
        self.assertEqual(result['brokerage'], {'name': 'Own Brokerage', 'license_number': '2222222'})
        self.assertEqual(query.await_count, 2)
        self.assertIn('user_id=eq.agent-owner', query.call_args_list[0].args[0])
        self.assertIn('id=eq.agent-owner', query.call_args_list[1].args[0])

    def test_active_own_organization_supplies_identity_not_source_host(self):
        own = {'id': 'own-office', 'name': 'Linked Office', 'license_number': '3333333',
               'contact_name': 'Own Broker', 'contact_email': 'broker@example.test'}
        query = AsyncMock(side_effect=[[PROFILE], [{'brokerage_id': 'own-office'}],
                                      [{'id': 'membership'}], [own]])
        with patch.object(MODULE, '_get', query):
            result = asyncio.run(MODULE._representation_professional_context(USER))
        self.assertEqual(result['brokerage'], own)
        membership = query.call_args_list[2].args[0]
        self.assertIn('user_id=eq.agent-owner', membership)
        self.assertIn('brokerage_id=eq.own-office', membership)
        self.assertIn('status=eq.active', membership)
        self.assertIn('id=eq.own-office&is_active=eq.true', query.call_args_list[3].args[0])

    def test_inactive_or_missing_organization_uses_profile_without_contact_leak(self):
        for tail in ([[]], [[{'id': 'membership'}], []]):
            query = AsyncMock(side_effect=[[PROFILE], [{'brokerage_id': 'old-office'}], *tail])
            with self.subTest(tail=tail), patch.object(MODULE, '_get', query):
                result = asyncio.run(MODULE._representation_professional_context(USER))
            self.assertEqual(result['brokerage'], {'name': 'Own Brokerage', 'license_number': '2222222'})
            self.assertNotIn('contact_email', result['brokerage'])

    def test_missing_profile_does_not_invent_identity(self):
        with patch.object(MODULE, '_get', AsyncMock(return_value=[])):
            result = asyncio.run(MODULE._representation_professional_context(USER))
        self.assertEqual(result, {'profile': {}, 'brokerage': {'name': '', 'license_number': ''}})

    def test_query_failure_is_not_mistaken_for_an_empty_profile(self):
        with patch.object(MODULE, '_get', AsyncMock(side_effect=RuntimeError('unavailable'))), \
             self.assertRaisesRegex(RuntimeError, 'unavailable'):
            asyncio.run(MODULE._representation_professional_context(USER))

    def test_broker_plan_cannot_use_the_source_host_or_infer_agent_as_broker(self):
        agreement = {'brokerage_id': 'foreign-library-host', 'form_code': 'TXR-1507',
                     'client_names': ['Client'], 'agreement_data': {'signer_plan': 'clients_and_broker'}}
        query = AsyncMock(side_effect=[[PROFILE], []])
        with patch.object(MODULE, '_get', query), self.assertRaisesRegex(ValueError, 'broker contact email'):
            asyncio.run(MODULE._standalone_signing_recipients(USER, agreement, ['client@example.test']))
        self.assertFalse(any('foreign-library-host' in call.args[0] for call in query.call_args_list))

    def test_associate_plan_works_without_seat_and_exposes_one_render_context(self):
        agreement = {'brokerage_id': 'foreign-library-host', 'form_code': 'TXR-1507',
                     'client_names': ['Client'], 'agreement_data': {'signer_plan': 'clients_and_associate'}}
        query = AsyncMock(side_effect=[[PROFILE], []])
        context = {}
        with patch.object(MODULE, '_get', query):
            result = asyncio.run(MODULE._standalone_signing_recipients(
                USER, agreement, ['client@example.test'], professional_context=context))
        self.assertEqual(result[-1], {'id': 'associate', 'name': 'Own Agent', 'email': USER['email']})
        self.assertEqual(context['brokerage']['name'], 'Own Brokerage')
        self.assertFalse(any('foreign-library-host' in call.args[0] for call in query.call_args_list))


if __name__ == '__main__':
    unittest.main()
