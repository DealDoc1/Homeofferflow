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
        self.assertLessEqual(implemented_form_codes(), checked)
        self.assertIn('security invoker', sql.lower())
        self.assertIn("set search_path = ''", sql.lower())
        self.assertIn('from public, anon, authenticated', sql.lower())


if __name__ == '__main__':
    unittest.main()
