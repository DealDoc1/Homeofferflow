"""Explicit broker contacts for owned agreements, with no seat requirement."""
import asyncio
import unittest
from unittest.mock import AsyncMock, patch
from tests.test_standalone_recipient_preview import MODULE, USER, AGREEMENT_ID, showing_draft

PROFILE = {'agent_name': 'Agent', 'brokerage_name': 'Independent Office', 'brokerage_license': '1234567'}
CONTACT = {'name': 'Broker One', 'email': 'broker@example.test'}


class IndependentBrokerSignerTests(unittest.TestCase):
    def test_preview_asks_for_broker_details_instead_of_blocking_no_seat_agent(self):
        draft = showing_draft('broker_and_clients')
        with patch.object(MODULE, '_get', AsyncMock(side_effect=[[draft], [PROFILE], []])):
            result = asyncio.run(MODULE._standalone_signing_recipient_preview(USER, AGREEMENT_ID))
        self.assertEqual(result['recipients'][-1], {
            'id': 'broker', 'name': '', 'email': '', 'emailEditable': True,
            'nameEditable': True, 'label': 'Broker signer'})

    def test_saved_request_shows_locked_broker_contact(self):
        draft = showing_draft('broker_and_clients')
        draft['agreement_data']['broker_signer'] = CONTACT
        draft['agreement_data']['_hof_signature_delivery'] = {'version': 1, 'document_id': 'saved'}
        draft['signwell_document_id'] = 'saved'
        with patch.object(MODULE, '_get', AsyncMock(side_effect=[[draft], [PROFILE], []])):
            result = asyncio.run(MODULE._standalone_signing_recipient_preview(USER, AGREEMENT_ID))
        broker = result['recipients'][-1]
        self.assertEqual(broker['name'], CONTACT['name'])
        self.assertEqual(broker['email'], CONTACT['email'])
        self.assertFalse(broker['emailEditable'])
        self.assertNotIn('nameEditable', broker)

    def test_entered_contact_supported_for_all_four_professional_forms(self):
        for code, plan in [('TXR-1501', 'clients_and_broker'), ('TXR-1507', 'clients_and_broker'),
                           ('TXR-1506', 'consumers_and_broker'), ('TXR-1508', 'broker_and_clients')]:
            draft = showing_draft(plan)
            draft['form_code'] = code
            context = {}
            with self.subTest(code=code), patch.object(MODULE, '_get', AsyncMock(side_effect=[[PROFILE], []])):
                result = asyncio.run(MODULE._standalone_signing_recipients(
                    USER, draft, ['client@example.test'], broker_signer=CONTACT, professional_context=context))
            self.assertEqual(result[-1], {'id': 'broker', **CONTACT})
            self.assertEqual(context['brokerage']['name'], 'Independent Office')
            self.assertEqual(context['broker_signer'], CONTACT)
            self.assertNotIn('broker_signer', draft['agreement_data'])

    def test_malformed_contacts_are_rejected(self):
        for bad in ([], {}, {'name': ' ', 'email': 'b@example.test'},
                    {'name': 'x'*121, 'email': 'b@example.test'}, {'name': ['Broker'], 'email': 'b@example.test'},
                    {'name': 'Broker\nBCC', 'email': 'b@example.test'},
                    {'name': 'Broker', 'email': 'invalid'}, {'name': 'Broker', 'email': 12},
                    {'name': 'Broker', 'email': 'x'*250+'@example.test'}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                MODULE._parse_broker_signer(bad)
        self.assertEqual(MODULE._parse_broker_signer({'name': ' Broker ', 'email': ' b@example.test '}),
                         {'name': 'Broker', 'email': 'b@example.test'})

    def test_contact_cannot_override_the_agent_or_a_buyer_seller_only_packet(self):
        for code, plan in [('TXR-1507', 'clients_and_associate'), ('TXR-1953', '')]:
            draft = showing_draft(plan)
            draft['form_code'] = code
            query = AsyncMock()
            with self.subTest(code=code), patch.object(MODULE, '_get', query), \
                 self.assertRaisesRegex(ValueError, 'separate broker signer'):
                asyncio.run(MODULE._standalone_signing_recipients(USER, draft, ['client@example.test'], broker_signer=CONTACT))
            query.assert_not_awaited()

    def test_existing_office_contact_cannot_be_silently_overridden(self):
        context = {'profile': PROFILE, 'brokerage': {'contact_name': 'Saved', 'contact_email': 'saved@example.test'}}
        with patch.object(MODULE, '_representation_professional_context', AsyncMock(return_value=context)), \
             self.assertRaisesRegex(ValueError, 'already saved'):
            asyncio.run(MODULE._standalone_signing_recipients(
                USER, showing_draft('broker_and_clients'), ['client@example.test'], broker_signer=CONTACT))


if __name__ == '__main__':
    unittest.main()
