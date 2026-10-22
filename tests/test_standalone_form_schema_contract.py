"""Keep implemented document codes compatible with persisted draft constraints."""

import ast
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def implemented_form_codes():
    tree = ast.parse((ROOT / 'api/admin-dashboard.py').read_text(encoding='utf-8'))
    constants = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            continue
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            constants[target.id] = node.value.value
        if target.id == 'TXR_SIGNING_FORM_CODES':
            return {constants[element.id] for element in node.value.elts}
    raise AssertionError('The implemented document code registry was not found.')


class StandaloneFormSchemaContractTests(unittest.TestCase):
    def test_every_implemented_document_can_be_stored_by_the_latest_constraint(self):
        pattern = re.compile(
            r'add\s+constraint\s+hof_standalone_agreements_form_code_check\s+'
            r'check\s*\(\s*form_code\s+in\s*\((.*?)\)\s*\)',
            re.IGNORECASE | re.DOTALL,
        )
        allowed = None
        for path in sorted((ROOT / 'supabase/migrations').glob('*.sql')):
            matches = pattern.findall(path.read_text(encoding='utf-8'))
            if matches:
                allowed = set(re.findall(r"'([^']+)'", matches[-1]))
        self.assertIsNotNone(allowed, 'The persisted draft form constraint must be recorded.')
        self.assertLessEqual(implemented_form_codes(), allowed)

    def test_live_readiness_checks_the_same_implemented_document_codes(self):
        definitions = [path.read_text(encoding='utf-8')
                       for path in sorted((ROOT / 'supabase/migrations').glob('*.sql'))
                       if 'create or replace function public.hof_release_schema_readiness()'
                       in path.read_text(encoding='utf-8').lower()]
        self.assertTrue(definitions)
        sql = definitions[-1]
        match = re.search(r'foreach supported_form_code in array array\[(.*?)\]', sql, re.DOTALL)
        self.assertIsNotNone(match, 'Release readiness must check actual draft form capabilities.')
        checked = set(re.findall(r"'([^']+)'", match.group(1)))
        # The already deployed v1/v2 contracts are immutable. The additive v3
        # delegates v2 and verifies newly supported codes against the constraint.
        wrapper = (ROOT/'supabase/migrations/20261019000034_bind_disclosure_to_listing_signature.sql').read_text()
        self.assertIn('baseline := public.hof_seller_disclosure_schema_readiness();', wrapper)
        self.assertIn("'homeofferflow-release-schema-v3'", wrapper)
        self.assertIn('strpos(constraint_definition,quote_literal(', wrapper)
        self.assertIn("'form_code:hof_standalone_agreements.TXR-1101'", wrapper)
        self.assertIn('security invoker', wrapper.lower())
        self.assertIn('set search_path=pg_catalog', wrapper.lower())
        self.assertIn('from public,anon,authenticated', wrapper.lower())
        checked.update(re.findall(r"quote_literal\('([^']+)'\)", wrapper))
        lease = (ROOT/'supabase/migrations/20261020231654_add_txr1102_lease_listing_drafts.sql').read_text()
        self.assertIn('baseline := public.hof_release_schema_readiness();', lease)
        self.assertIn("'homeofferflow-lease-listing-schema-v1'", lease)
        self.assertIn('c.convalidated', lease)
        self.assertIn('security invoker', lease.lower())
        self.assertIn('set search_path=pg_catalog', lease.lower())
        self.assertIn('from public,anon,authenticated', lease.lower())
        checked.update(re.findall(r"quote_literal\('([^']+)'\)", lease))
        self.assertLessEqual(implemented_form_codes(), checked)
        self.assertIn('security invoker', sql.lower())
        self.assertIn("set search_path = ''", sql.lower())
        self.assertIn('from public, anon, authenticated', sql.lower())


if __name__ == '__main__':
    unittest.main()
