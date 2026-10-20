"""Private composition only: no database, provider, invitations or credentials."""
from copy import deepcopy
from dataclasses import replace
from io import BytesIO
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from pypdf import PdfReader
from reportlab.pdfgen.canvas import Canvas

from lib import purchase_disclosure_execution as module
from lib.seller_disclosure_explanations import RENDER_REVISION
from lib.seller_questionnaire import required_answers


USER = '11111111-1111-4111-8111-111111111111'
OFFER = '22222222-2222-4222-8222-222222222222'
DRAFT = '33333333-3333-4333-8333-333333333333'
REVISION = '44444444-4444-4444-8444-444444444444'
OTHER = '55555555-5555-4555-8555-555555555555'


def blank_pdf(count):
    output = BytesIO()
    canvas = Canvas(output, pagesize=(612, 792))
    for index in range(count):
        canvas.drawString(40, 750, f'FICTIONAL TEST SOURCE {index + 1}')
        canvas.showPage()
    canvas.save()
    return output.getvalue()


def fixture(*, buyers=1, sellers=1, water=False, long=False):
    names = ['Élodie QA 李', 'Second QA Seller'][:sellers]
    main, well = required_answers(water)
    draft = {'id': DRAFT, 'agent_user_id': USER, 'brokerage_id': OTHER,
        'seller_names': names, 'buyer_names': [], 'status': 'draft',
        'property_address': '123 QA Road, Dallas, TX 75201',
        'review_content_revision': REVISION, 'seller_review_attested': True,
        'seller_review_render_revision': RENDER_REVISION,
        'disclosure_source_id': OTHER, 'disclosure_source_revision': '05-04-2026',
        'water_source_id': OFFER if water else None,
        'water_source_revision': '05-04-2026' if water else None,
        'response_data': dict.fromkeys(main, 'N'), 'water_rights_data': dict.fromkeys(well, 'U')}
    if long:
        draft['response_data']['notes'] = 'Fictional seller explanation: café, 東京, roof repairs. ' * 35
    offer = {'buyer1': 'QA Buyer One', 'buyerEmail': 'buyer-one@example.com',
        'address': '123 QA Road', 'city': 'Dallas', 'state': 'TX', 'zip': '75201',
        'seller': names[0], 'seller2Name': names[1] if sellers == 2 else ''}
    if buyers == 2:
        offer.update(buyer2='QA Buyer Two', buyer2Email='buyer-two@example.com')
    links = [{'id': str(index), 'draft_id': DRAFT, 'agent_user_id': USER, 'brokerage_id': OTHER,
        'seller_index': index, 'seller_name': name, 'seller_attested_name': name,
        'seller_email': f'seller-{index}@example.com', 'seller_attested_at': '2026-10-20T13:00:00Z',
        'review_content_revision': REVISION, 'review_render_revision': RENDER_REVISION}
        for index, name in enumerate(names, 1)]
    return {'id': OFFER, 'user_id': USER, 'offer_data': offer}, draft, links


class PurchaseDisclosureExecutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        main, water = os.environ.get('HOF_QA_DISCLOSURE_SOURCE'), os.environ.get('HOF_QA_WATER_SOURCE')
        cls.actual_sources = bool(main and water)
        cls.main_pdf = Path(main).read_bytes() if cls.actual_sources else blank_pdf(4)
        cls.water_pdf = Path(water).read_bytes() if cls.actual_sources else blank_pdf(2)

    def setUp(self):
        if not self.actual_sources:
            self.source_patch = patch('lib.trec_seller_disclosure.validate_source_bytes')
            self.source_patch.start()
            self.addCleanup(self.source_patch.stop)

    def prepare(self, case=None, retry=False, **options):
        record, draft, links = deepcopy(case or fixture(**options))
        return module.prepare_execution(record, draft, links, user_id=USER,
            source_pdf=self.main_pdf, water_pdf=self.water_pdf if draft.get('water_source_id') else None, for_retry=retry)

    def test_all_one_two_buyer_seller_water_cases_have_exact_roles_and_calibrated_fields(self):
        for buyers in (1, 2):
            for sellers in (1, 2):
                for water in (False, True):
                    with self.subTest(buyers=buyers, sellers=sellers, water=water):
                        plan = self.prepare(buyers=buyers, sellers=sellers, water=water)
                        self.assertEqual(len(PdfReader(BytesIO(plan.pdf)).pages),
                            (6 if water else 4) + len(plan.continuation_pages))
                        expected = {'1', '2'} if buyers == 2 else {'1'}
                        expected |= {'3', '4'} if sellers == 2 else {'3'}
                        self.assertEqual({row['id'] for row in plan.recipients}, expected)
                        self.assertEqual({field['recipient_id'] for field in plan.fields}, expected)
                        for field in plan.fields:
                            if '_buyer' in field['api_id']:
                                self.assertIn(field['recipient_id'], {'1', '2'})
                            if '_seller' in field['api_id']:
                                self.assertIn(field['recipient_id'], {'3', '4'})
                            if field['type'] == 'date':
                                self.assertEqual(field['height'], 18)
                        self.assertEqual(plan.binding['offer_id'], OFFER)
                        self.assertEqual(plan.binding['fingerprint'], plan.content_fingerprint)

    def test_reversed_sellers_follow_offer_ids_and_verified_review_email_not_alias(self):
        record, draft, links = fixture(sellers=2)
        record['offer_data'].update(seller=draft['seller_names'][1], seller2Name=draft['seller_names'][0],
                                    seller1Email='unapproved@example.com')
        plan = self.prepare((record, draft, links))
        self.assertEqual([(r['id'], r['email']) for r in plan.recipients],
            [('1', 'buyer-one@example.com'), ('3', 'seller-2@example.com'), ('4', 'seller-1@example.com')])
        self.assertEqual({f['recipient_id'] for f in plan.fields if '_seller1_' in f['api_id']}, {'4'})

    def test_missing_pending_or_separately_sent_disclosure_is_not_ready(self):
        record, draft, links = fixture()
        with self.assertRaises(module.DisclosureNotReady):
            module.prepare_execution(record, None, [], user_id=USER, source_pdf=self.main_pdf)
        for change in ({'status': 'signed'}, {'seller_review_attested': False},
            {'seller_review_render_revision': 'old'}, {'signwell_document_id': 'existing'},
            {'signature_packet_id': OTHER}, {'signature_offer_id': OTHER},
            {'response_data': {'_hof_signature_delivery': {}}}, {'response_data': {}},
            {'buyer_names': ['Prior buyer']}, {'disclosure_source_revision': 'old'}):
            with self.subTest(change=change), self.assertRaises(module.DisclosureNotReady):
                self.prepare((record, {**draft, **change}, links))

    def test_wrong_owners_or_unsaved_offer_are_rejected(self):
        record, draft, links = fixture()
        for row, disclosure in (({**record, 'user_id': OTHER}, draft),
                                (record, {**draft, 'agent_user_id': OTHER}),
                                ({**record, 'id': None}, draft)):
            with self.assertRaises(PermissionError): self.prepare((row, disclosure, links))
        with self.assertRaises(module.DisclosureNotReady):
            self.prepare(({**record, 'signwell_document_id': 'already-sent'}, draft, links))
        tracked = {**record, 'offer_data': {**record['offer_data'], '_hof_signature_delivery': {}}}
        with self.assertRaises(module.DisclosureNotReady): self.prepare((tracked, draft, links))
        for status in ('Deleted','Buyer Signed','Rejected'):
            with self.subTest(status=status), self.assertRaises(module.DisclosureNotReady):
                self.prepare(({**record, 'status': status}, draft, links))

    def test_current_attestation_is_required_for_each_exact_seller(self):
        record, draft, links = fixture(sellers=2)
        for key, value in (('draft_id', OTHER), ('agent_user_id', OTHER), ('brokerage_id', OFFER),
            ('seller_index', True), ('seller_index', 1), ('seller_name', 'Other'),
            ('seller_attested_name', 'Other'), ('seller_attested_at', None),
            ('review_content_revision', OTHER), ('review_render_revision', 'old'), ('revoked_at', 'yesterday')):
            changed = deepcopy(links); changed[1][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(module.DisclosureNotReady):
                self.prepare((record, draft, changed))
        for changed in (links[:1], links + [links[0]], []):
            with self.assertRaises(module.DisclosureNotReady): self.prepare((record, draft, changed))

    def test_wrong_address_unit_duplicate_or_different_sellers_do_not_match(self):
        record, draft, links = fixture(sellers=2)
        for change in ({'property_address': '124 QA Road, Dallas, TX 75201'},
            {'property_address': '123 QA Road Apt 2, Dallas, TX 75201'},
            {'seller_names': ['Another seller']}, {'seller_names': ['Same', 'Same']}):
            with self.subTest(change=change), self.assertRaises(module.DisclosureNotReady):
                self.prepare((record, {**draft, **change}, links))

    def test_duplicate_or_missing_signing_emails_are_rejected(self):
        record, draft, links = fixture(buyers=2)
        for email in ('buyer-one@example.com', 'buyer-two@example.com', '', 'bad'):
            changed = deepcopy(links); changed[0]['seller_email'] = email
            with self.subTest(email=email), self.assertRaises(ValueError): self.prepare((record, draft, changed))
        record['offer_data']['buyer2Email'] = 'BUYER-ONE@example.com'
        with self.assertRaises(ValueError): self.prepare((record, draft, links))

    def test_water_cannot_be_silently_missing_or_implicitly_added(self):
        for water in (False, True):
            record, draft, links = fixture(water=water)
            with self.assertRaises(module.DisclosureNotReady):
                module.prepare_execution(record, draft, links, user_id=USER, source_pdf=self.main_pdf,
                    water_pdf=None if water else self.water_pdf)

    def test_long_unicode_continuation_has_all_four_labeled_initial_rows(self):
        plan = self.prepare(buyers=2, sellers=2, water=True, long=True)
        reader = PdfReader(BytesIO(plan.pdf))
        self.assertGreater(len(reader.pages), 6)
        for page in plan.continuation_pages:
            text = reader.pages[page - 1].extract_text()
            for label in ('Seller 1 initials', 'Seller 2 initials', 'Purchaser 1 initials', 'Purchaser 2 initials'):
                self.assertIn(label, text)
            self.assertEqual({f['recipient_id'] for f in plan.fields if f['page'] == page}, {'1', '2', '3', '4'})
        self.assertIn('café', ' '.join(page.extract_text() for page in reader.pages))

    def test_append_offsets_without_mutating_the_plan_and_preserves_each_page(self):
        plan = self.prepare(buyers=2, sellers=2, water=True, long=True)
        original_fields = deepcopy(plan.fields)
        merged, fields = module.append_execution(blank_pdf(12), plan)
        pages = PdfReader(BytesIO(merged)).pages
        source = PdfReader(BytesIO(plan.pdf)).pages
        self.assertEqual(len(pages), 12 + len(source))
        self.assertEqual([p.extract_text() for p in pages[12:]], [p.extract_text() for p in source])
        self.assertEqual([f['page'] for f in fields], [f['page'] + 12 for f in original_fields])
        self.assertEqual(plan.fields, original_fields)
        with self.assertRaises(ValueError): module.append_execution(blank_pdf(12), replace(plan, pdf=plan.pdf + b'changed'))

    def test_fingerprint_is_stable_and_binds_answers_review_and_recipient_destination(self):
        case = fixture()
        plan = self.prepare(case)
        self.assertEqual(plan.content_fingerprint, self.prepare(case).content_fingerprint)
        for kind in ('answer', 'review', 'recipient'):
            record, draft, links = deepcopy(case)
            if kind == 'answer': draft['response_data']['roof_type'] = 'Metal'
            if kind == 'review':
                draft['review_content_revision'] = OTHER
                for link in links: link['review_content_revision'] = OTHER
            if kind == 'recipient': links[0]['seller_email'] = 'new-confirmed@example.com'
            self.assertNotEqual(plan.content_fingerprint, self.prepare((record, draft, links)).content_fingerprint)

    def test_retry_reconstructs_only_the_same_server_bound_review_and_document(self):
        case = fixture(buyers=2, sellers=2, water=True, long=True)
        plan = self.prepare(case)
        record, draft, links = deepcopy(case)
        record.update(signwell_document_id='saved-document', status='Sent for Signature')
        record['offer_data']['_hof_signature_delivery'] = {'document_id': 'saved-document', 'seller_disclosure': deepcopy(plan.binding)}
        draft['signature_offer_id'] = OFFER
        restored = self.prepare((record, draft, links), retry=True)
        self.assertEqual(restored.binding, plan.binding)
        self.assertEqual(restored.fields, plan.fields)
        with self.assertRaises(module.DisclosureNotReady): self.prepare((record, draft, links))
        for change in ('document', 'binding', 'association'):
            current, disclosure = deepcopy(record), deepcopy(draft)
            if change == 'document': current['signwell_document_id'] = 'another-document'
            if change == 'binding': current['offer_data']['_hof_signature_delivery']['seller_disclosure']['fingerprint'] = 'changed'
            if change == 'association': disclosure['signature_offer_id'] = OTHER
            with self.subTest(change=change), self.assertRaises(module.DisclosureNotReady):
                self.prepare((current, disclosure, links), retry=True)


if __name__ == '__main__': unittest.main()
