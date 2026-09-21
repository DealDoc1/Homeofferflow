import copy
import unittest
from lib.offer_signwell_delivery import offer_answers, stable_delivery_answers


class StableDeliveryAnswersTests(unittest.TestCase):
    def setUp(self):
        self.original = {'buyerEmail': 'buyer@example.test', 'price': 100,
                         'repairsText': 'Agreed repairs', 'generatedAt': 'original',
                         '_signing_source_hashes': ['source-v1'],
                         '_signing_render_revisions': ['render-v1'],
                         'uploadedDisclosureDocs': [{'base64': 'original-bytes'}]}
        self.record = {'signwell_document_id': 'doc', 'offer_data': copy.deepcopy(self.original)}

    def test_known_display_bookkeeping_reuses_exact_original_inputs(self):
        current = {**self.original, 'generatedAt': 'new', 'packetGeneratedAt': 'new',
                   'packetGenerationError': 'temporary error', '_savedFromDashboard': True}
        result = stable_delivery_answers(current, self.record)
        self.assertEqual(result, offer_answers(self.original))
        result['uploadedDisclosureDocs'][0]['base64'] = 'mutated'
        self.assertEqual(self.record['offer_data'], self.original)

    def test_changes_to_terms_recipients_attachments_and_sources_remain_significant(self):
        for key, value in [('buyerEmail','different@example.test'), ('price',200),
                           ('repairsText','Different repairs'), ('_signing_source_hashes',['source-v2']),
                           ('_signing_render_revisions',['render-v2']),
                           ('uploadedDisclosureDocs',[{'base64':'different-bytes'}]),
                           ('unknownField','must-not-ignore')]:
            with self.subTest(key=key):
                current = {**self.original, key: value, 'generatedAt':'new'}
                self.assertEqual(stable_delivery_answers(current,self.record), offer_answers(current))

    def test_untracked_or_missing_record_does_not_reuse_old_inputs(self):
        current = {**self.original, 'generatedAt': 'new'}
        for record in (None, {}, {'offer_data':self.original}, 'invalid'):
            self.assertEqual(stable_delivery_answers(current,record), offer_answers(current))

    def test_json_types_are_not_treated_as_identical_answers(self):
        self.record['offer_data']['price'] = 0
        current = {**self.record['offer_data'], 'price':False, 'generatedAt':'new'}
        self.assertEqual(stable_delivery_answers(current,self.record)['generatedAt'], 'new')


if __name__ == '__main__':
    unittest.main()
