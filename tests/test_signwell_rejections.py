import json
from types import SimpleNamespace
import unittest

from lib.signwell_rejections import SigningCreateRejected, rejection_diagnostic, safe_field_path


def response(status=422, errors=None):
    return SimpleNamespace(status_code=status, content=b'{}', json=lambda:{'errors': errors})


class SignWellRejectionTests(unittest.TestCase):
    def test_field_paths_are_preserved_without_error_values(self):
        result = rejection_diagnostic(response(errors={'fields[0][14].height':['secret client data'], 'recipients.0.email':['secret@example.test']}))
        self.assertEqual(result, {'http_status':422,'category':'signature_fields','fields':['fields.0.14.height','recipients.0.email']})
        self.assertNotIn('secret',json.dumps(result))

    def test_unknown_nested_keys_cannot_leak_client_data(self):
        result = rejection_diagnostic(response(errors={'metadata.private@example.test':'private value','secret@example.test':'secret', 'fields.<script>':'raw'}))
        self.assertEqual(result['fields'],['fields','metadata'])
        self.assertNotIn('private',json.dumps(result)); self.assertNotIn('script',json.dumps(result))

    def test_status_and_schema_categories_are_local_constants(self):
        cases=[(401,{},'service_authentication'),(403,{},'service_authentication'),(402,{},'service_account'),
               (413,{},'packet_size'),(429,{},'rate_limit'),(422,{'files.0.file_base64':'private'},'packet_file'),
               (422,{'recipients.0.email':'private'},'signer_details'),(422,{'unknown':'private'},'request_validation'),
               (500,{},'request_rejected')]
        for status,errors,category in cases:
            with self.subTest(status=status,category=category):
                self.assertEqual(rejection_diagnostic(response(status,errors))['category'],category)

    def test_array_error_format_is_supported_without_echoing_messages(self):
        result = rejection_diagnostic(response(errors=[{'field':'recipients[0].email','message':'private'}, {'path':'fields.0.1.page','value':'private'}]))
        self.assertEqual(result['fields'],['fields.0.1.page','recipients.0.email'])
        self.assertNotIn('private',json.dumps(result))

    def test_malformed_or_large_provider_responses_do_not_leak(self):
        malformed=SimpleNamespace(status_code=422,content=b'not json',json=lambda:(_ for _ in ()).throw(ValueError('private')))
        large=SimpleNamespace(status_code=422,content=b'x'*65537,json=lambda:(_ for _ in ()).throw(AssertionError('Do not parse large body')))
        for r in [malformed,large]:self.assertEqual(rejection_diagnostic(r)['fields'],[])

    def test_customer_message_and_code_never_use_provider_text(self):
        error=SigningCreateRejected(response(errors={'recipients.0.email':['private@example.test']}))
        self.assertEqual(error.code,'signwell_signer_details')
        self.assertIn('Check the names and email addresses',str(error))
        self.assertIn('No invitation was requested',str(error))
        self.assertNotIn('private',str(error))

    def test_path_and_output_limits(self):
        self.assertIsNone(safe_field_path('x'*10000))
        result=rejection_diagnostic(response(errors={f'fields.0.{i}.page':'private' for i in range(64)}))
        self.assertLessEqual(len(result['fields']),16)

    def test_nested_error_objects_retain_only_known_schema_paths(self):
        result = rejection_diagnostic(response(errors={
            'fields': [[{'height': ['private geometry value']}]],
            'recipients': [{'email': ['private@example.test']}],
            'files': [{'file_base64': ['private PDF contents']}],
        }))
        self.assertEqual(result['fields'], ['fields.0.0.height', 'files.0.file_base64', 'recipients.0.email'])
        self.assertNotIn('private', json.dumps(result))

    def test_nested_private_keys_and_values_are_not_diagnostic_paths(self):
        result = rejection_diagnostic(response(errors={
            'fields': [{'private@example.test': {'email': 'private value'}}],
            'metadata': {'client private name': 'private value'},
        }))
        self.assertEqual(result['fields'], ['fields', 'metadata'])
        self.assertNotIn('private', json.dumps(result))

    def test_nested_walk_has_bounded_work_and_output(self):
        errors = {'fields': [[{'height': ['private value']}] for _ in range(1000)]}
        result = rejection_diagnostic(response(errors=errors))
        self.assertLessEqual(len(result['fields']), 16)
        self.assertLess(len(json.dumps(result)), 650)
        self.assertNotIn('private', json.dumps(result))


if __name__=='__main__':unittest.main()
