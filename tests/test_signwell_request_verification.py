"""A provider draft must retain the exact reviewed fields and recipients."""
import copy
import unittest

from lib.signwell_request import document_matches_signing_request as matches


class RequestVerificationTests(unittest.TestCase):
    def setUp(self):
        self.fields = [[{'api_id': 'signature-1', 'recipient_id': 'buyer',
                        'type': 'signature', 'page': 1, 'x': 20, 'y': 30,
                        'width': 100, 'height': 25}]]
        self.recipients = [{'id': 'buyer', 'name': 'Test Buyer', 'email': 'buyer@example.com'}]
        self.document = copy.deepcopy({'fields': self.fields, 'recipients': self.recipients})

    def check(self):
        return matches(self.document, self.fields, self.recipients)

    def test_serialized_geometry_and_email_case_are_supported(self):
        self.document['fields'][0][0]['x'] = '20.1'
        self.document['recipients'][0]['email'] = 'BUYER@example.com'
        self.assertTrue(self.check())

    def test_duplicate_fields_cannot_hide_an_extra_signature(self):
        self.document['fields'].append(copy.deepcopy(self.fields[0]))
        self.assertFalse(self.check())

    def test_duplicate_expected_fields_are_also_invalid(self):
        self.fields[0].append(copy.deepcopy(self.fields[0][0]))
        self.assertFalse(self.check())

    def test_unidentified_or_malformed_extra_fields_are_rejected(self):
        for field in ({'type': 'signature'}, None, 'signature'):
            with self.subTest(field=field):
                self.document['fields'] = [self.fields[0] + [field]]
                self.assertFalse(self.check())

    def test_nonfinite_and_changed_geometry_are_rejected(self):
        for value in ('NaN', 'Infinity', '-Infinity', 900, None):
            with self.subTest(value=value):
                self.document['fields'][0][0]['x'] = value
                self.assertFalse(self.check())

    def test_changed_signer_identity_is_rejected(self):
        for key in ('name', 'email', 'id'):
            with self.subTest(key=key):
                self.document['recipients'] = copy.deepcopy(self.recipients)
                self.document['recipients'][0][key] = 'different'
                self.assertFalse(self.check())

    def test_duplicate_or_malformed_recipients_are_rejected(self):
        for recipients in (self.recipients * 2, [None], {}, None, [{'id': ''}]):
            with self.subTest(recipients=recipients):
                self.document['recipients'] = recipients
                self.assertFalse(self.check())

    def test_malformed_field_groups_and_documents_are_rejected(self):
        for fields in (None, {}, [None], [self.fields[0][0]]):
            self.document['fields'] = fields
            self.assertFalse(self.check())
        self.assertFalse(matches(None, self.fields, self.recipients))
