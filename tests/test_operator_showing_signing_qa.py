import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

from lib import showing_signing_qa as qa

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('admin_showing_qa', ROOT / 'api/admin-dashboard.py')
MODULE = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MODULE)
USER = {'id': 'd36ed4b3-7179-4b56-99c4-a709b1b847cb', 'email': 'andrewchri@gmail.com'}
SCENARIO = [{'id': '807eba14-0ebc-4d0a-96c6-e5ddd69a5b02'}]
DOC = '574177e8-b381-45c8-a7ec-e3fe71b0d22b'


def response(code, value=None, content=b''):
    return SimpleNamespace(status_code=code, content=content, json=lambda: value)


class OperatorShowingSigningQATests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.client = AsyncMock(); self.client.__aenter__.return_value = self.client
        self.source = {'id': 'source', 'source_revision': '02-25-26', 'source_sha256': qa.SOURCE_SHA256,
                       'storage_bucket': 'PRIVATE_BUCKET', 'storage_path': 'PRIVATE_PATH'}
        patches = [patch.object(MODULE, 'SIGNWELL_ENABLED', True), patch.object(MODULE, 'SIGNWELL_API_KEY', 'PRIVATE_KEY'),
                   patch.object(MODULE, '_is_platform_admin', AsyncMock(return_value=True)),
                   patch.object(MODULE, '_get', AsyncMock(side_effect=[SCENARIO, [], [self.source]])),
                   patch.object(MODULE, '_patch', AsyncMock()),
                   patch.object(MODULE.httpx, 'AsyncClient', return_value=self.client),
                   patch.object(qa, 'build_packet', return_value=(b'%PDF synthetic', [[{'type': 'initials'}]], [])),
                   patch.object(qa, 'build_payload', return_value={'name': qa.DOCUMENT_PREFIX + '30cf21f132f8', 'test_mode': True})]
        for p in patches: p.start(); self.addCleanup(p.stop)

    async def test_private_source_then_reserved_single_test_and_redacted_receipt(self):
        self.client.get.return_value = response(200, content=b'%PDF source')
        self.client.post.side_effect = [response(201, [{'id': 'run'}]), response(201, {'id': DOC, 'test_mode': True, 'status': 'Sent', 'embedded_signing_url': 'SECRET_LINK'})]
        result = await MODULE._showing_signing_qa(USER, send=True)
        self.assertEqual(result['phase'], 'created'); self.assertEqual(result['document_id'], DOC)
        self.assertIn('/storage/v1/object/', self.client.get.call_args.args[0])
        self.assertIn('/hof_qa_runs', self.client.post.call_args_list[0].args[0])
        self.assertEqual(self.client.post.call_args_list[0].kwargs['json']['release_name'], qa.QA_REVISION)
        self.assertNotIn('PRIVATE_KEY', str(result)); self.assertNotIn('SECRET_LINK', str(MODULE._patch.call_args))
        self.assertNotIn('PRIVATE_PATH', str(MODULE._patch.call_args))

    async def test_recorded_attempt_does_not_download_source_or_send_again(self):
        MODULE._get.side_effect = [SCENARIO, [{'id': 'run', 'notes': json.dumps({'qa_revision': qa.QA_REVISION, 'phase': 'started'})}]]
        result = await MODULE._showing_signing_qa(USER, send=True)
        self.assertEqual(result['phase'], 'started'); self.client.get.assert_not_called(); self.client.post.assert_not_called()

    async def test_existing_showing_document_status_is_read_only(self):
        MODULE._get.side_effect = [SCENARIO, [{'id': 'run', 'notes': json.dumps({'qa_revision': qa.QA_REVISION, 'phase': 'created', 'document_id': DOC, 'test_mode': True})}]]
        self.client.get.return_value = response(200, {'id': DOC, 'test_mode': True, 'name': qa.DOCUMENT_PREFIX + '30cf21f132f8',
            'metadata': {'qa_revision': qa.QA_REVISION}, 'recipients': list(qa.QA_RECIPIENTS), 'status': 'Completed'})
        result = await MODULE._showing_signing_qa(USER)
        self.assertEqual(result['provider_status'], 'completed'); self.assertIn('visual review', result['message'])
        self.client.post.assert_not_called(); MODULE._patch.assert_not_called(); qa.build_packet.assert_not_called()

    async def test_wrong_or_missing_source_stops_before_reservation(self):
        for sources in [[], [{**self.source, 'source_sha256': 'different'}], [{**self.source, 'source_revision': 'old'}]]:
            with self.subTest(sources=sources):
                MODULE._get.side_effect = [SCENARIO, [], sources]
                with self.assertRaises(ValueError): await MODULE._showing_signing_qa(USER, send=True)
                self.client.post.assert_not_called()

    async def test_failed_source_download_is_safe_and_does_not_reserve(self):
        self.client.get.return_value = response(403, content=b'PRIVATE_KEY')
        with self.assertRaisesRegex(ValueError, 'Nothing was sent'): await MODULE._showing_signing_qa(USER, send=True)
        self.client.post.assert_not_called()

    async def test_source_exception_never_leaks_credentials_or_paths(self):
        self.client.get.side_effect = RuntimeError('PRIVATE_KEY PRIVATE_PATH SECRET_LINK')
        with self.assertRaises(ValueError) as caught: await MODULE._showing_signing_qa(USER, send=True)
        self.assertNotIn('PRIVATE_KEY', str(caught.exception)); self.assertNotIn('PRIVATE_PATH', str(caught.exception))
        self.client.post.assert_not_called()

    async def test_concurrent_reservation_loser_never_reaches_provider(self):
        MODULE._get.side_effect = [SCENARIO, [], [self.source], [{'id': 'winner', 'notes': json.dumps({'qa_revision': qa.QA_REVISION, 'phase': 'started'})}]]
        self.client.get.return_value = response(200, content=b'%PDF source')
        self.client.post.return_value = response(409, {})
        result = await MODULE._showing_signing_qa(USER, send=True)
        self.assertEqual(result['run_id'], 'winner'); self.assertEqual(self.client.post.await_count, 1)
        MODULE._patch.assert_not_called()

    async def test_foreign_purchase_name_cannot_satisfy_showing_test_identity(self):
        MODULE._get.side_effect = [SCENARIO, [{'id': 'run', 'notes': json.dumps({'qa_revision': qa.QA_REVISION, 'phase': 'created', 'document_id': DOC, 'test_mode': True})}]]
        self.client.get.return_value = response(200, {'id': DOC, 'test_mode': True, 'name': 'QA ONLY - purchase placement - old',
            'metadata': {'qa_revision': qa.QA_REVISION}, 'recipients': list(qa.QA_RECIPIENTS), 'status': 'Completed'})
        result = await MODULE._showing_signing_qa(USER)
        self.assertIn('did not match', result['message']); self.assertNotEqual(result['provider_status'], 'completed')
        self.client.post.assert_not_called()

    async def test_owner_and_admin_checks_precede_source_access(self):
        with self.assertRaises(PermissionError): await MODULE._showing_signing_qa({**USER, 'email': 'other@example.test'}, send=True)
        MODULE._get.assert_not_called(); self.client.get.assert_not_called()
        MODULE._is_platform_admin.return_value = False
        with self.assertRaises(PermissionError): await MODULE._showing_signing_qa(USER, send=True)
        MODULE._get.assert_not_called()

    def test_showing_route_rejects_all_custom_settings_after_admin_check(self):
        source = (ROOT / 'api/admin-dashboard.py').read_text()
        start = source.index('if data.get("action") in {"send_showing_signing_test", "check_showing_signing_test"}')
        self.assertLess(source.index('if not asyncio.run(_is_platform_admin(user)):', source.index('def do_POST')), start)
        self.assertIn('if set(data) != {"action"}', source[start:start + 500])
