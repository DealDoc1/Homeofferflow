import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

from lib import amendment_signing_qa as qa

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('admin_amendment_qa', ROOT / 'api/admin-dashboard.py')
MODULE = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MODULE)
USER = {'id': 'd36ed4b3-7179-4b56-99c4-a709b1b847cb', 'email': 'andrewchri@gmail.com'}
SCENARIO = [{'id': '807eba14-0ebc-4d0a-96c6-e5ddd69a5b02'}]
DOC = '574177e8-b381-45c8-a7ec-e3fe71b0d22b'


def response(code, value=None, content=b''):
    return SimpleNamespace(status_code=code, content=content, json=lambda: value)


class OperatorAmendmentSigningQATests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.client = AsyncMock(); self.client.__aenter__.return_value = self.client
        self.source = {'source_revision': '05-04-2026', 'source_sha256': qa.SOURCE_SHA256,
                       'storage_bucket': 'PRIVATE_BUCKET', 'storage_path': 'PRIVATE_PATH'}
        for item in [patch.object(MODULE, 'SIGNWELL_ENABLED', True), patch.object(MODULE, 'SIGNWELL_API_KEY', 'PRIVATE_KEY'),
                     patch.object(MODULE, '_is_platform_admin', AsyncMock(return_value=True)),
                     patch.object(MODULE, '_get', AsyncMock(side_effect=[SCENARIO, [], [self.source]])),
                     patch.object(MODULE, '_patch', AsyncMock()),
                     patch.object(MODULE.httpx, 'AsyncClient', return_value=self.client),
                     patch.object(qa, 'build_packet', return_value=(b'%PDF synthetic', [[{'type': 'signature'}]], [])),
                     patch.object(qa, 'build_payload', return_value={'name': qa.DOCUMENT_PREFIX + 'ee90d4d627b6', 'test_mode': True})]:
            item.start(); self.addCleanup(item.stop)

    async def test_exact_private_source_reservation_then_one_send_without_secret_leaks(self):
        self.client.get.return_value = response(200, content=b'%PDF source')
        self.client.post.side_effect = [response(201, [{'id': 'run'}]), response(201, {'id': DOC, 'test_mode': True, 'status': 'Sent', 'embedded_signing_url': 'SECRET_LINK'})]
        result = await MODULE._amendment_signing_qa(USER, send=True)
        self.assertEqual(result['phase'], 'created')
        self.assertIn('/hof_qa_runs', self.client.post.call_args_list[0].args[0])
        self.assertEqual(self.client.post.await_count, 2)
        self.assertEqual(self.client.post.call_args_list[0].kwargs['json']['release_name'], qa.QA_REVISION)
        for secret in ['PRIVATE_KEY', 'PRIVATE_PATH', 'SECRET_LINK']:
            self.assertNotIn(secret, str(result)); self.assertNotIn(secret, str(MODULE._patch.call_args))

    async def test_recorded_attempt_and_reservation_race_never_duplicate_send(self):
        recorded = [{'id': 'winner', 'notes': json.dumps({'qa_revision': qa.QA_REVISION, 'phase': 'started'})}]
        MODULE._get.side_effect = [SCENARIO, recorded]
        result = await MODULE._amendment_signing_qa(USER, send=True)
        self.assertEqual(result['phase'], 'started'); self.client.get.assert_not_called(); self.client.post.assert_not_called()
        MODULE._get.side_effect = [SCENARIO, [], [self.source], recorded]
        self.client.get.return_value = response(200, content=b'%PDF source')
        self.client.post.return_value = response(409, {})
        result = await MODULE._amendment_signing_qa(USER, send=True)
        self.assertEqual(result['run_id'], 'winner'); self.assertEqual(self.client.post.await_count, 1)

    async def test_check_reads_only_the_exact_provider_test_and_not_the_source(self):
        recorded = [{'id': 'run', 'notes': json.dumps({'qa_revision': qa.QA_REVISION, 'phase': 'created', 'document_id': DOC, 'test_mode': True})}]
        MODULE._get.side_effect = [SCENARIO, recorded]
        self.client.get.return_value = response(200, {'id': DOC, 'test_mode': True, 'name': qa.DOCUMENT_PREFIX + 'ee90d4d627b6',
            'metadata': {'qa_revision': qa.QA_REVISION}, 'recipients': list(qa.QA_RECIPIENTS), 'status': 'Completed'})
        result = await MODULE._amendment_signing_qa(USER)
        self.assertEqual(result['provider_status'], 'completed'); self.assertFalse(result['visual_review_passed'])
        self.client.post.assert_not_called(); qa.build_packet.assert_not_called(); MODULE._patch.assert_not_called()
        MODULE._get.side_effect = [SCENARIO, recorded]
        self.client.get.return_value.json = lambda: {'id': DOC, 'test_mode': False, 'status': 'Completed'}
        result = await MODULE._amendment_signing_qa(USER)
        self.assertIn('did not match', result['message'])

    async def test_source_mismatch_or_download_failure_prevents_reservation(self):
        for source in [[], [{**self.source, 'source_revision': 'old'}], [{**self.source, 'source_sha256': 'wrong'}]]:
            MODULE._get.side_effect = [SCENARIO, [], source]
            with self.assertRaises(ValueError): await MODULE._amendment_signing_qa(USER, send=True)
            self.client.post.assert_not_called()
        MODULE._get.side_effect = [SCENARIO, [], [self.source]]
        self.client.get.side_effect = RuntimeError('PRIVATE_KEY PRIVATE_PATH')
        with self.assertRaises(ValueError) as error: await MODULE._amendment_signing_qa(USER, send=True)
        self.assertNotIn('PRIVATE_KEY', str(error.exception)); self.client.post.assert_not_called()

    async def test_owner_and_platform_admin_checks_precede_all_source_access(self):
        with self.assertRaises(PermissionError): await MODULE._amendment_signing_qa({**USER, 'email': 'other@example.test'}, send=True)
        MODULE._get.assert_not_called()
        MODULE._is_platform_admin.return_value = False
        with self.assertRaises(PermissionError): await MODULE._amendment_signing_qa(USER, send=True)
        MODULE._get.assert_not_called(); self.client.get.assert_not_called()
