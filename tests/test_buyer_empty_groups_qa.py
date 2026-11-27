"""Provider-confirmed empty-group correction without resetting prior QA."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import os
import json
import base64
import httpx
import unittest
from unittest.mock import AsyncMock, patch

from lib import buyer_representation_signing_qa as buyer
from lib.signwell_qa_transport import create_qa_document
from tests.test_operator_purchase_signing_qa import MODULE, DOCUMENT_ID, USER, response

ROOT = Path(__file__).resolve().parents[1]


def specimens():
    packet = b'%PDF-fictional'
    fields = [[{'api_id': 'signature', 'type': 'signature', 'recipient_id': 'qa_a',
                'page': 1, 'x': 10, 'y': 10, 'width': 100, 'height': 20, 'required': True}]]
    with patch.object(buyer, 'PACKET_SHA256', sha256(packet).hexdigest()), \
         patch.object(buyer, 'layout_fingerprint', return_value=buyer.LAYOUT_SHA256):
        old = buyer.build_default_message_draft_payload(packet, fields, buyer.REVIEWED_SOURCE_COMMIT)
        new = buyer.build_empty_groups_payload(packet, fields, buyer.REVIEWED_SOURCE_COMMIT)
    return old, new


class BuyerEmptyGroupsTests(unittest.TestCase):
    def test_changes_only_empty_groups_and_new_reservation_identity(self):
        old, new = specimens()
        self.assertEqual(old['checkbox_groups'], [])
        self.assertNotIn('checkbox_groups', new)
        self.assertNotIn('message', new)
        self.assertIs(new['draft'], True)
        self.assertIs(new['test_mode'], True)
        self.assertIs(new['apply_signing_order'], False)
        self.assertEqual(new['conditional_rules'], [])
        self.assertEqual(new['metadata']['qa_revision'], buyer.EMPTY_GROUPS_QA_REVISION)
        self.assertNotIn(buyer.EMPTY_GROUPS_QA_REVISION, {buyer.QA_REVISION, buyer.DEFAULT_MESSAGE_QA_REVISION})
        self.assertEqual({**new, 'checkbox_groups': [], 'name': old['name'],
                          'metadata': {**new['metadata'], 'qa_revision': buyer.DEFAULT_MESSAGE_QA_REVISION}}, old)

    def test_never_discards_nonempty_completion_controls(self):
        groups = [{'group_name': 'required_choice'}]
        with patch.object(buyer, 'build_default_message_draft_payload', return_value={
            'checkbox_groups': groups, 'metadata': {},
        }):
            payload = buyer.build_empty_groups_payload(b'fixture', [], buyer.REVIEWED_SOURCE_COMMIT)
        self.assertEqual(payload['checkbox_groups'], groups)

    def test_owner_control_starts_disabled_and_keeps_legacy_controls(self):
        html = (ROOT / 'index.html').read_text()
        owner = html.index("${['andrewchri@gmail.com', 'andrew@ondemanddfw.com'].includes")
        start = html.index('<button id="adminBuyerEmptyGroupsSigningTestSend"')
        self.assertGreater(start, owner)
        self.assertIn('disabled>', html[start:html.index('</button>', start)])
        self.assertIn("runPurchaseSigningTest(false, this, 'buyer-empty-groups')", html)
        self.assertIn('create_buyer_package_default_message_draft', html)
        self.assertIn('send_buyer_package_signing_test', html)


class BuyerEmptyGroupsProtocolTests(unittest.IsolatedAsyncioTestCase):
    @unittest.skipUnless(os.environ.get('HOF_BUYER_QA_SOURCE_DIR'), 'Private reviewed sources not supplied')
    async def test_actual_source_wire_omits_only_empty_groups_and_preserves_exact_pdf(self):
        sources = buyer.load_sources(Path(os.environ['HOF_BUYER_QA_SOURCE_DIR']), buyer.IABS_SHA256)
        packet, fields, _ = buyer.build_packet(sources)
        payload = buyer.build_empty_groups_payload(packet, fields, buyer.REVIEWED_SOURCE_COMMIT)
        seen = []
        def inspect(request):
            wire = json.loads(request.content)
            self.assertNotIn('checkbox_groups', wire)
            self.assertNotIn('message', wire)
            self.assertEqual(wire['fields'], fields)
            self.assertEqual(sha256(base64.b64decode(wire['files'][0]['file_base64'])).hexdigest(), buyer.PACKET_SHA256)
            self.assertEqual(buyer.layout_fingerprint(packet, fields), buyer.LAYOUT_SHA256)
            self.assertIs(wire['draft'], True)
            self.assertIs(wire['test_mode'], True)
            seen.append(request.url)
            return httpx.Response(201, json={'id': DOCUMENT_ID, 'test_mode': True})
        async with httpx.AsyncClient(transport=httpx.MockTransport(inspect)) as client:
            await create_qa_document(client, api_key='fictional-key', payload=payload)
        self.assertEqual(len(seen), 1)

    async def test_adapter_uses_separate_identity_without_changing_previous_recipes(self):
        async def inspect(user, *, send, _spec):
            self.assertEqual(user, USER)
            self.assertFalse(send)
            self.assertEqual(_spec.QA_REVISION, buyer.EMPTY_GROUPS_QA_REVISION)
            self.assertEqual(_spec.DOCUMENT_PREFIX, buyer.EMPTY_GROUPS_DOCUMENT_PREFIX)
            self.assertIs(_spec.build_payload, buyer.build_empty_groups_payload)
            self.assertTrue(_spec.VERIFY_DRAFT)
            self.assertEqual(_spec.QA_RECIPIENTS, buyer.QA_RECIPIENTS)
            self.assertEqual(_spec.REVIEWED_SOURCE_COMMIT, buyer.REVIEWED_SOURCE_COMMIT)
            return {'phase': 'not_started'}
        with patch.object(MODULE, '_purchase_signing_qa', inspect):
            result = await MODULE._buyer_package_signing_qa(USER, empty_groups=True)
        self.assertEqual(result['phase'], 'not_started')

    async def test_absent_empty_groups_still_require_verified_readback_before_send(self):
        _, payload = specimens()
        document = {'id': DOCUMENT_ID, 'test_mode': True, 'name': payload['name'],
                    'status': 'draft', 'apply_signing_order': False,
                    'metadata': deepcopy(payload['metadata']), 'fields': deepcopy(payload['fields']),
                    'recipients': deepcopy(payload['recipients']), 'checkbox_groups': [], 'conditional_rules': []}
        for altered in (False, True):
            returned = deepcopy(document)
            if altered:
                returned['fields'][0][0]['required'] = False
            client = AsyncMock()
            client.get.return_value = response(200, returned)
            client.post.return_value = response(200, {'id': DOCUMENT_ID, 'test_mode': True, 'status': 'sent'})
            receipt = {'document_id': DOCUMENT_ID}
            with self.subTest(altered=altered), patch.object(MODULE, '_patch', AsyncMock()), \
                 patch.object(MODULE, 'SIGNWELL_API_KEY', 'fictional-key'):
                await MODULE._verify_and_send_fixed_qa_draft(client, 'fictional-run', receipt, payload)
            if altered:
                client.post.assert_not_awaited()
                self.assertEqual(receipt['phase'], 'draft_unverified')
            else:
                self.assertTrue(receipt['controls_verified'])
                self.assertEqual(receipt['phase'], 'created')
                client.post.assert_awaited_once()
