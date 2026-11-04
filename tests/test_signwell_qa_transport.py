"""Inspect actual serialized HTTP requests without any network/provider writes."""
from copy import deepcopy
import base64
from hashlib import sha256
import json
import os
from pathlib import Path
import unittest
from unittest.mock import AsyncMock, patch

import httpx

from lib import purchase_signing_qa as qa
from lib.signwell_qa_transport import TRANSPORT_REVISION, create_qa_document, send_verified_qa_draft
from tests.test_operator_purchase_signing_qa import MODULE, USER, SCENARIO, DOCUMENT_ID


class SignwellQATransportTests(unittest.IsolatedAsyncioTestCase):
    @unittest.skipUnless(os.environ.get('HOF_BUYER_QA_SOURCE_DIR'), 'Private reviewed buyer sources not supplied')
    async def test_actual_packet_survives_full_request_serialization_byte_for_byte(self):
        from lib import buyer_representation_signing_qa as buyer
        sources = buyer.load_sources(Path(os.environ['HOF_BUYER_QA_SOURCE_DIR']), buyer.IABS_SHA256)
        packet, fields, _ = buyer.build_packet(sources)
        payload = buyer.build_payload(packet, fields, buyer.REVIEWED_SOURCE_COMMIT)
        seen = []
        def transport(request):
            data = json.loads(request.content)
            decoded = base64.b64decode(data['files'][0]['file_base64'], validate=True)
            self.assertEqual(sha256(decoded).hexdigest(), buyer.PACKET_SHA256)
            self.assertTrue(data['fields'] == fields)
            self.assertEqual(int(request.headers['content-length']), len(request.content))
            self.assertIs(data['test_mode'], True); self.assertIs(data['draft'], True)
            self.assertEqual(data['metadata']['qa_transport_revision'], TRANSPORT_REVISION)
            self.assertTrue(buyer.QA_REVISION.endswith('-v2'))
            seen.append(len(request.content))
            return httpx.Response(201, json={'id': DOCUMENT_ID, 'test_mode': True})
        async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as client:
            await create_qa_document(client, api_key='fixture-key', payload=payload)
        self.assertEqual(len(seen), 1)

    async def test_create_uses_canonical_json_and_explicit_test_header_without_mutation(self):
        seen = []
        def transport(request):
            seen.append(request)
            return httpx.Response(201, json={'id': DOCUMENT_ID, 'test_mode': True})
        payload = {'test_mode': True, 'draft': True, 'apply_signing_order': False,
                   'files': [{'file_base64': 'QA'}], 'fields': [[{'required': True}]]}
        original = deepcopy(payload)
        async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as client:
            result = await create_qa_document(client, api_key='fixture-key', payload=payload)
        self.assertEqual(result.status_code, 201)
        self.assertEqual(len(seen), 1)
        request = seen[0]
        self.assertEqual(str(request.url), 'https://www.signwell.com/api/v1/documents')
        self.assertEqual(request.headers['accept'], 'application/json')
        self.assertEqual(request.headers['content-type'], 'application/json')
        self.assertEqual(request.headers['x-testmode-enabled'], 'true')
        self.assertEqual(request.headers['x-api-key'], 'fixture-key')
        self.assertEqual(json.loads(request.content), original)
        self.assertEqual(payload, original)

    async def test_send_uses_canonical_document_path_with_same_options(self):
        seen = []
        def transport(request):
            seen.append(request); return httpx.Response(200, json={'test_mode': True})
        payload = {'test_mode': True, 'reminders': False, 'apply_signing_order': False}
        async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as client:
            await send_verified_qa_draft(client, DOCUMENT_ID, api_key='fixture-key', payload=payload)
        self.assertEqual(str(seen[0].url), 'https://www.signwell.com/api/v1/documents/' + DOCUMENT_ID + '/send')
        self.assertEqual(seen[0].headers['x-testmode-enabled'], 'true')
        self.assertEqual(json.loads(seen[0].content), payload)

    async def test_malformed_or_live_mode_never_reaches_transport(self):
        client = AsyncMock()
        for payload in (None, {}, {'test_mode': False}, {'test_mode': 1}, {'test_mode': 'true'}):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                await create_qa_document(client, api_key='fixture-key', payload=payload)
            with self.subTest(send_payload=payload), self.assertRaises(ValueError):
                await send_verified_qa_draft(client, DOCUMENT_ID, api_key='fixture-key', payload=payload)
        client.post.assert_not_called()

    async def test_redirect_is_not_followed_even_if_client_default_allows_it(self):
        seen = []
        def transport(request):
            seen.append(request)
            return httpx.Response(307, headers={'location': 'https://other.example.test/collect'})
        async with httpx.AsyncClient(transport=httpx.MockTransport(transport), follow_redirects=True) as client:
            result = await create_qa_document(client, api_key='fixture-key', payload={'test_mode': True})
            self.assertEqual(result.status_code, 307)
            result = await send_verified_qa_draft(client, DOCUMENT_ID, api_key='fixture-key', payload={'test_mode': True})
            self.assertEqual(result.status_code, 307)
        self.assertEqual(len(seen), 2)
        self.assertTrue(all(request.url.host == 'www.signwell.com' for request in seen))

    async def test_rejected_create_is_returned_once_without_retry(self):
        seen = []
        def transport(request):
            seen.append(request); return httpx.Response(400, json={'errors': {'files': ['not accepted']}})
        async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as client:
            result = await create_qa_document(client, api_key='fixture-key', payload={'test_mode': True})
        self.assertEqual(result.status_code, 400); self.assertEqual(len(seen), 1)

    async def test_invalid_connection_or_document_id_fails_without_exposing_key(self):
        client = AsyncMock()
        for key in (None, '', '   ', 1):
            with self.subTest(key=key), self.assertRaises(ValueError):
                await create_qa_document(client, api_key=key, payload={'test_mode': True})
        with self.assertRaises(ValueError) as error:
            await send_verified_qa_draft(client, '../foreign', api_key='PRIVATE_KEY', payload={'test_mode': True})
        self.assertNotIn('PRIVATE_KEY', str(error.exception)); client.post.assert_not_called()

    async def test_coordinator_rejects_live_payload_before_reserving_attempt(self):
        with patch.object(MODULE, 'SIGNWELL_ENABLED', True), \
             patch.object(MODULE, 'SIGNWELL_API_KEY', 'fixture-key'), \
             patch.object(MODULE, '_is_platform_admin', AsyncMock(return_value=True)), \
             patch.object(MODULE, '_get', AsyncMock(side_effect=[SCENARIO, []])), \
             patch.object(MODULE.httpx, 'AsyncClient') as client, \
             patch.object(qa, 'build_packet', return_value=(b'QA', [[]], [])), \
             patch.object(qa, 'build_payload', return_value={'test_mode': False}):
            with self.assertRaisesRegex(ValueError, 'explicit test mode'):
                await MODULE._purchase_signing_qa(USER, send=True)
            client.assert_not_called()


if __name__ == '__main__':
    unittest.main()
