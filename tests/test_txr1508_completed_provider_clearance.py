"""Printed-rule guard calibrated from recovered completed nonbinding QA."""
import unittest
from lib.txr_1508 import build_signwell_fields_txr1508


# Observed provider image transform from multiple recovered completed-QA anchors.
# It includes the provider's one-pixel origin padding, not merely 0.75 scaling.
PROVIDER_POINT_PER_PIXEL = 0.7528125
PRINTED_RULE_TOP = {'agent': 518.17, 'client1': 560.29, 'client2': 604.00}


class Txr1508CompletedProviderClearanceTests(unittest.TestCase):
    def test_acknowledgement_ink_finishes_above_each_source_rule(self):
        fields = build_signwell_fields_txr1508({'signer_plan': 'associate_and_clients'}, client_count=2)[0]
        for field in fields:
            role = next(role for role in PRINTED_RULE_TOP if f'_{role}_' in field['api_id'])
            bottom = (field['y'] - 1 + field['height']) * PROVIDER_POINT_PER_PIXEL
            with self.subTest(field=field['api_id']):
                self.assertLess(bottom, PRINTED_RULE_TOP[role], 'Provider ink must not cross the printed rule or the next sentence.')

    def test_broker_and_associate_use_the_same_calibrated_source_rows(self):
        associate = build_signwell_fields_txr1508({'signer_plan': 'associate_and_clients'}, client_count=2)[0]
        broker = build_signwell_fields_txr1508({'signer_plan': 'broker_and_clients'}, client_count=2)[0]
        self.assertEqual([{k:v for k,v in f.items() if k != 'recipient_id'} for f in associate],
                         [{k:v for k,v in f.items() if k != 'recipient_id'} for f in broker])
