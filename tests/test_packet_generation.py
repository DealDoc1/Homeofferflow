import hashlib
import unittest
from unittest.mock import Mock

from lib.packet_generation import (PacketGenerationStore, PacketGenerationPending,
    PacketAllowanceUnavailable, PacketGenerationBusy, packet_answers_hash, render_packet_with_usage)


class MemoryPacketStore:
    """Protocol double only; SQL ownership/locking is tested in PostgreSQL."""
    def __init__(self):
        self.rows = {}
        self.completions = 0

    def claim(self, user, offer, digest, token):
        key = 'hof-packet-v1-' + hashlib.sha256(f'{user}:{offer}:{digest}'.encode()).hexdigest()
        if key not in self.rows:
            self.rows[key] = {'user_id': user, 'offer_id': offer, 'answers_hash': digest,
                'generation_key': key, 'status': 'reserved', 'outcome': 'reserved',
                'billing_month': '2026-09', 'attempt_token': token, 'usage_event_id': None}
        return dict(self.rows[key])

    def complete(self, row):
        saved = self.rows[row['generation_key']]
        if saved['status'] != 'completed':
            self.completions += 1
            saved.update(status='completed', outcome='completed',
                         usage_event_id='77777777-7777-4777-8777-777777777777', attempt_token=None)
        return dict(saved)

    def release(self, row):
        saved = self.rows[row['generation_key']]
        if saved['status'] != 'reserved' or saved['attempt_token'] != row['attempt_token']:
            return False
        del self.rows[row['generation_key']]
        return True


class PacketGenerationTests(unittest.TestCase):
    def setUp(self):
        self.user = '11111111-1111-4111-8111-111111111111'
        self.offer = '22222222-2222-4222-8222-222222222222'
        self.hash = 'a' * 64
        self.render = Mock(return_value=b'%PDF-fixture')
        self.store = Mock()
        self.row = None
        self.store.claim.side_effect = self.claim
        self.store.complete.side_effect = self.complete
        self.store.release.return_value = True

    def claim(self, user, offer, digest, token):
        if self.row is None:
            self.row = {'user_id': user, 'offer_id': offer, 'answers_hash': digest,
                'generation_key': 'hof-packet-v1-' + hashlib.sha256(f'{user}:{offer}:{digest}'.encode()).hexdigest(),
                'status': 'reserved', 'outcome': 'reserved', 'billing_month': '2026-09',
                'attempt_token': token, 'usage_event_id': None}
        return dict(self.row)

    def complete(self, row):
        self.row.update(status='completed',outcome='completed',usage_event_id='77777777-7777-4777-8777-777777777777',attempt_token=None)
        return dict(self.row)

    def run_packet(self):
        return render_packet_with_usage(user_id=self.user, offer_id=self.offer,
            answers_hash=self.hash, render=self.render, store=self.store)

    def test_completion_is_recorded_before_caller_receives_pdf(self):
        result = self.run_packet()
        self.assertEqual(result['pdf_bytes'], b'%PDF-fixture')
        self.assertEqual(result['usage']['status'], 'recorded')
        self.store.complete.assert_called_once()
        self.store.release.assert_not_called()

    def test_completed_retry_does_not_record_second_usage_or_release(self):
        self.run_packet()
        self.assertTrue(self.run_packet()['usage']['recovered'])
        self.store.complete.assert_called_once()
        self.store.release.assert_not_called()

    def test_denied_or_busy_reservation_never_renders(self):
        for outcome, error in [('no_subscription',PacketAllowanceUnavailable), ('inactive',PacketAllowanceUnavailable),
                               ('limit_reached',PacketAllowanceUnavailable), ('busy',PacketGenerationBusy),
                               ('legacy_packet',PacketGenerationPending),
                               ('not_owned',PacketGenerationPending)]:
            self.store.claim.side_effect = None
            self.store.claim.return_value = {'outcome': outcome}
            with self.assertRaises(error): self.run_packet()
        self.render.assert_not_called()
        self.store.complete.assert_not_called()

    def test_render_failure_releases_only_uncompleted_reservation(self):
        self.render.side_effect = ValueError('Rendering failed')
        with self.assertRaises(ValueError): self.run_packet()
        self.store.release.assert_called_once()
        self.store.complete.assert_not_called()

    def test_invalid_pdf_is_not_charged(self):
        self.render.return_value = b'not a pdf'
        with self.assertRaises(ValueError): self.run_packet()
        self.store.release.assert_called_once()
        self.store.complete.assert_not_called()

    def test_uncertain_completion_never_returns_pdf_or_refunds_possibly_completed_work(self):
        self.store.complete.side_effect = PacketGenerationPending('timeout')
        with self.assertRaises(PacketGenerationPending): self.run_packet()
        self.store.release.assert_not_called()

    def test_stale_worker_cannot_report_success(self):
        self.store.complete.side_effect = lambda row: {**row, 'outcome': 'stale_attempt'}
        with self.assertRaises(PacketGenerationPending): self.run_packet()
        self.store.release.assert_not_called()

    def test_changed_period_cannot_report_success(self):
        self.store.complete.side_effect = lambda row: {**self.complete(row), 'billing_month': '2026-10'}
        with self.assertRaises(PacketGenerationPending): self.run_packet()
        self.store.release.assert_not_called()

    def test_allowance_identity_ignores_only_lifecycle_and_server_bookkeeping(self):
        offer = {'buyer1': 'Buyer', 'price': '100', 'uploadedDisclosureDocs': [{'base64': 'original'}]}
        original = packet_answers_hash(offer)
        self.assertEqual(original, packet_answers_hash({**offer, 'generatedAt': 'later',
            'packetGenerationError': 'timeout', '_signing_source_hashes': ['fixed-source'],
            '_signing_render_revisions': {'TXR-1953': 'fixed'}, 'signwell': {'id': 'provider'}}))
        self.assertNotEqual(original, packet_answers_hash({**offer, 'price': '200'}))
        self.assertNotEqual(original, packet_answers_hash({**offer, 'uploadedDisclosureDocs': [{'base64': 'changed'}]}))

    def test_wrong_identity_from_store_never_renders(self):
        original_claim = self.claim
        self.store.claim.side_effect = lambda *args: {**original_claim(*args), 'user_id': 'another-user'}
        with self.assertRaises(PacketGenerationPending): self.run_packet()
        self.render.assert_not_called()

    def test_invalid_identity_does_not_touch_database(self):
        self.user = 'unverified'
        with self.assertRaises(ValueError): self.run_packet()
        self.store.claim.assert_not_called()

    def test_adapter_uses_service_only_rpc_and_no_browser_month_or_quantity(self):
        client = Mock()
        client.post.return_value.status_code = 200
        client.post.return_value.json.return_value = {'outcome': 'busy'}
        store = PacketGenerationStore(supabase_url='https://db.example.test',service_key='test-only',client=client)
        result = store.claim(self.user,self.offer,self.hash,'attempt')
        self.assertEqual(result['outcome'], 'busy')
        request = client.post.call_args
        self.assertEqual(request.args[0], 'https://db.example.test/rest/v1/rpc/hof_claim_packet_generation')
        self.assertEqual(request.kwargs['headers']['Authorization'], 'Bearer test-only')
        self.assertEqual(set(request.kwargs['json']), {'p_user','p_offer','p_answers_hash','p_attempt'})
        client.post.return_value.status_code = 500
        with self.assertRaises(PacketGenerationPending): store.claim(self.user,self.offer,self.hash,'attempt')


if __name__ == '__main__': unittest.main()
