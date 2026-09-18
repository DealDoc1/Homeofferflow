"""Current property-condition choice must control the generated contract."""
from io import BytesIO
import unittest
from unittest.mock import patch

from pypdf import PdfReader
from tests.test_controlled_launch import adapter, configure_local_forms, minimal_offer


class RepairElectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        configure_local_forms()

    def render(self, choice, text):
        offer = minimal_offer(repairsText=text)
        if choice is None:
            offer.pop('asIs')
        else:
            offer['asIs'] = choice
        with patch.object(adapter.verified, 'build_pages_data', wraps=adapter.verified.build_pages_data) as pages:
            pdf = adapter.fill_and_merge_20_19(offer)
        # The renderer's actual property-condition argument drives the two
        # mutually exclusive checkbox entries on page 5.
        args = pages.call_args.args
        import inspect
        bound = inspect.signature(pages._mock_wraps).bind(*args, **pages.call_args.kwargs)
        return bound.arguments['as_is'], PdfReader(BytesIO(pdf)).pages[4].extract_text()

    def test_explicit_as_is_does_not_include_old_repair_answer(self):
        for choice in ['yes', ' YES ', True, '1']:
            with self.subTest(choice=choice):
                election, page = self.render(choice, 'QA_REPAIR_OLD_TERM')
                self.assertEqual(election, 'yes')
                self.assertNotIn('QA_REPAIR_OLD_TERM', page)

    def test_repairs_election_keeps_current_repair_terms(self):
        for choice in ['repairs', 'no', 'seller repairs']:
            with self.subTest(choice=choice):
                election, page = self.render(choice, 'QA_REPAIR_CURRENT_TERM')
                self.assertEqual(election, 'repairs')
                self.assertIn('QA_REPAIR_CURRENT_TERM', page)

    def test_legacy_text_only_draft_retains_repairs(self):
        election, page = self.render(None, 'QA_REPAIR_LEGACY_TERM')
        self.assertEqual(election, 'repairs')
        self.assertIn('QA_REPAIR_LEGACY_TERM', page)

    def test_no_choice_and_no_text_preserves_existing_default(self):
        election, _ = self.render(None, '')
        self.assertEqual(election, 'yes')
