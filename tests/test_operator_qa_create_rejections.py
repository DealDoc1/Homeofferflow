"""Real QA coordinator rejection capture without provider values or retries."""
import json
from unittest.mock import AsyncMock, patch
import unittest

from lib import purchase_signing_qa as qa
from tests.test_operator_purchase_signing_qa import MODULE, USER, SCENARIO, response


class OperatorQACreateRejectionTests(unittest.IsolatedAsyncioTestCase):
    async def invoke(self, rejected):
        client = AsyncMock(); client.__aenter__.return_value = client
        client.post.side_effect = [response(201, [{'id': 'reserved-run'}]), rejected]
        with patch.object(MODULE, 'SIGNWELL_ENABLED', True), \
             patch.object(MODULE, 'SIGNWELL_API_KEY', 'PRIVATE_KEY'), \
             patch.object(MODULE, '_is_platform_admin', AsyncMock(return_value=True)), \
             patch.object(MODULE, '_get', AsyncMock(side_effect=[SCENARIO, []])), \
             patch.object(MODULE, '_patch', AsyncMock()) as checkpoint, \
             patch.object(MODULE.httpx, 'AsyncClient', return_value=client), \
             patch.object(qa, 'build_packet', return_value=(b'fictional', [[]], [])):
            result = await MODULE._purchase_signing_qa(USER, send=True)
            notes = json.loads(checkpoint.call_args.args[2]['notes'])
        self.assertEqual(client.post.await_count, 2)
        client.get.assert_not_called()
        self.assertEqual(result['phase'], 'unconfirmed')
        self.assertNotIn('create_rejection', result)
        self.assertNotIn('PRIVATE_KEY', json.dumps(notes))
        return notes

    async def test_400_keeps_allowlisted_paths_and_discards_values(self):
        rejected = response(400, {'errors': {'conditional_rules': ['PRIVATE_MESSAGE'],
            'PRIVATE_CONTACT': 'PRIVATE_VALUE', 'files': [{'file_base64': 'PRIVATE_PDF'}]}})
        notes = await self.invoke(rejected)
        self.assertEqual(notes['create_rejection'], {'http_status': 400,
            'category': 'request_rejected', 'fields': ['conditional_rules', 'files.0.file_base64']})
        self.assertFalse(any(value in json.dumps(notes) for value in
            ('PRIVATE_MESSAGE', 'PRIVATE_CONTACT', 'PRIVATE_VALUE', 'PRIVATE_PDF')))

    async def test_malformed_response_keeps_status_without_raw_error(self):
        rejected = response(502, {})
        def invalid_json(): raise ValueError('PRIVATE_BODY')
        rejected.json = invalid_json
        notes = await self.invoke(rejected)
        self.assertEqual(notes['create_rejection'], {'http_status': 502,
            'category': 'request_rejected', 'fields': []})
        self.assertNotIn('PRIVATE_BODY', json.dumps(notes))


if __name__ == '__main__':
    unittest.main()
