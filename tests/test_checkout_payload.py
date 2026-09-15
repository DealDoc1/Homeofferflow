import copy
import hashlib
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from lib.checkout_payload import load_checkout_payload


class CheckoutPayloadTests(unittest.TestCase):
    def setUp(self):
        self.offer = {'_plan': 'self', '_paymentEmail': 'payer@example.test', 'repairsText': 'José 🏡\u2028李\u2029'}
        raw = json.dumps(self.offer, ensure_ascii=False)
        self.row = {'id': '11111111-1111-4111-8111-111111111111', 'payload_text': raw,
                    'payload_sha256': hashlib.sha256(raw.encode()).hexdigest(), 'stripe_session_id': 'cs_fixture'}
        self.session = {'id': 'cs_fixture', 'mode': 'payment', 'payment_status': 'paid',
                        'customer_email': 'payer@example.test', 'metadata': {
                            'plan': 'self', 'offer_payload_id': self.row['id'],
                            'offer_payload_sha256': self.row['payload_sha256']}}
        self.client = Mock()
        self.client.get.return_value = SimpleNamespace(status_code=200, json=lambda: [self.row])

    def load(self):
        return load_checkout_payload(self.session, supabase_url='https://db.example.test', service_key='fake', client=self.client)

    def test_exact_payload_and_bound_session_filter(self):
        self.assertEqual(self.load(), self.offer)
        self.assertEqual(self.client.get.call_args.kwargs['params']['stripe_session_id'], 'eq.cs_fixture')

    def test_zero_total_promotion_remains_supported(self):
        self.session['payment_status'] = 'no_payment_required'
        self.assertEqual(self.load(), self.offer)

    def test_invalid_or_unpaid_session_fails_before_read(self):
        for key, value in [('id', 'evil'), ('id', []), ('payment_status', 'unpaid'), ('mode', 'subscription')]:
            with self.subTest(key=key, value=value):
                original = copy.deepcopy(self.session)
                self.session[key] = value
                with self.assertRaises(ValueError): self.load()
                self.client.get.assert_not_called()
                self.session = original

    def test_invalid_reference_hash_or_plan_fails_before_read(self):
        for key, value in [('offer_payload_id', 'or=(id.neq.null)'), ('offer_payload_sha256', 'bad'), ('plan', 'seller')]:
            with self.subTest(key=key):
                original = copy.deepcopy(self.session)
                self.session['metadata'][key] = value
                with self.assertRaises(ValueError): self.load()
                self.client.get.assert_not_called()
                self.session = original

    def test_missing_duplicate_corrupt_and_unbound_records_fail_closed(self):
        for rows in [[], [self.row, self.row], [{**self.row, 'payload_text': '{}'}],
                     [{**self.row, 'stripe_session_id': None}], [{**self.row, 'stripe_session_id': 'cs_other'}],
                     [{**self.row, 'payload_sha256': 'b' * 64}], [{**self.row, 'id': 'other'}]]:
            with self.subTest(rows=len(rows)):
                self.client.get.return_value = SimpleNamespace(status_code=200, json=lambda: rows)
                with self.assertRaises(ValueError): self.load()

    def test_wrong_receipt_email_is_rejected(self):
        self.session['customer_email'] = 'another@example.test'
        with self.assertRaises(ValueError): self.load()

    def test_provider_failure_redacts_body(self):
        self.client.get.side_effect = RuntimeError('private payload and key')
        with self.assertRaisesRegex(ValueError, '^The saved checkout packet could not be verified') as caught: self.load()
        self.assertNotIn('private', str(caught.exception))

    def test_node_sender_runtime(self):
        result = subprocess.run(['node', '--test', 'tests/checkout_payload.runtime.cjs'],
                                cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
