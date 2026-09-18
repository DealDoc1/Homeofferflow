"""Measured lease-addendum blanks and lossless, party-initialed overflow."""
import base64
import copy
import importlib
from io import BytesIO
import unittest

import pdfplumber
from pypdf import PdfReader
from tests.test_txr_1953_renderer import blank_one_page_pdf
from tests.test_txr_render_send_snapshot import RenderSendFixture, USER
from tests.test_txr_signing_request_path import MODULE
from tests.test_controlled_launch import configure_local_forms, residential_lease_offer, one_page_pdf_base64
from lib import production_adapter as adapter


def sample(code, *, long=False, buyers=2, sellers=2):
    data = {'property_address': '100 QA Street, Frisco',
            'buyer_names': ['BuyerOne', 'BuyerTwo'][:buyers],
            'seller_names': ['SellerOne', 'SellerTwo'][:sellers],
            'delivery_choice': 'oral_notice'}
    if code == 1953:
        data.update(lease_status='assignment', oral_lease_notice='Tenant, rent and term as entered.',
                    delivery_days='365', explanation='No exceptions reported.')
    else:
        data.update(leased_fixture_types=['other'], leased_fixtures_other='Pool equipment',
                    assumed_fixture_leases=['other'], assumed_fixture_leases_other='Pool lease',
                    buyer_first_cost='2500.75', removal_choice='will_not',
                    oral_fixture_lease_notice='Lessee, rental amount and term as entered.')
    if long:
        # At or below saved-interview length limits, with long words and
        # literal markup that must not become ReportLab formatting.
        data['property_address'] = 'A' * 400
        data['buyer_names'] = [('José <b>李</b> & Buyer' + str(i) + 'N' * 180)[:180] for i in range(buyers)]
        data['seller_names'] = [('Ana <i>Seller</i> & ' + str(i) + 'S' * 180)[:180] for i in range(sellers)]
        if code == 1953:
            data['oral_lease_notice'] = 'O' * 500
            data['explanation'] = 'E' * 1200
        else:
            data.update(leased_fixtures_other='F' * 180, assumed_fixture_leases_other='L' * 180,
                        oral_fixture_lease_notice='O' * 500)
    return data


class LeaseAnswerBoundsTests(unittest.TestCase):
    def module(self, code):
        return importlib.import_module(f'lib.txr_{code}')

    def render(self, code, data):
        return getattr(self.module(code), f'render_txr_{code}')(blank_one_page_pdf(), data)

    def fields(self, code, data):
        return getattr(self.module(code), f'build_signwell_fields_txr{code}')(data)[0]

    def test_answers_fit_independently_measured_printed_blanks(self):
        cases = [(1953, {'property_address': 'Property', 'delivery_choice': 'not_received', 'explanation': 'Exception'},
                  {'Property': (241.32, 558, 107.64), '365': (101.88, 126.05, 305.8),
                   'Exception': (478.98, 569.88, 476.76), 'BuyerOne': (52.14, 281.88, 621.06),
                   'SellerOne': (330.6, 556.38, 621.06), 'BuyerTwo': (52.14, 281.88, 676.02),
                   'SellerTwo': (330.6, 556.38, 676.02)}),
                 (1953, {'oral_lease_notice': 'OralNotice'}, {'OralNotice': (101.88, 579.18, 336.42)}),
                 (1954, {'property_address': 'Property', 'leased_fixtures_other': 'Fixture',
                         'assumed_fixture_leases_other': 'Assumed', 'oral_fixture_lease_notice': 'OralNotice'},
                  {'Property': (241.32, 558, 130.68), 'Fixture': (474.9, 576.36, 200.70),
                   'Assumed': (98.76, 338.04, 261.60), '2500.75': (479.1, 577.56, 261.60),
                   'OralNotice': (454.5, 574.2, 459.30), 'BuyerOne': (47.76, 299.46, 599.58),
                   'SellerOne': (313.26, 556.38, 599.58), 'BuyerTwo': (47.76, 299.46, 676.62),
                   'SellerTwo': (313.26, 556.38, 676.62)})]
        for code, values, regions in cases:
            with pdfplumber.open(BytesIO(self.render(code, {**sample(code), **values}))) as pdf:
                words = pdf.pages[0].extract_words()
                for value, (left, right, rule) in regions.items():
                    with self.subTest(code=code, value=value):
                        word = next(w for w in words if w['text'] == value)
                        self.assertGreaterEqual(word['x0'], left)
                        self.assertLessEqual(word['x1'], right)
                        self.assertGreaterEqual(word['top'], rule - 12)
                        self.assertLess(word['bottom'], rule)

    def test_full_terms_survive_pagination_without_mutation_or_off_page_glyphs(self):
        for code in (1953, 1954):
            data = sample(code, long=True)
            original = copy.deepcopy(data)
            with pdfplumber.open(BytesIO(self.render(code, data))) as pdf:
                self.assertGreater(len(pdf.pages), 2)
                # Remove repeated headings/footer from reading order, not
                # individual glyphs from terms that could hide a loss.
                body = ''.join(''.join((p.crop((48, 140, 564, 682)).extract_text() or '').split())
                               for p in pdf.pages[1:])
                for value in self.module(code).answer_layout(data).overflow.values():
                    self.assertIn(''.join(value.split()), body)
                for page in pdf.pages[1:]:
                    self.assertIn(f'TXR-{code} CONTINUATION EXHIBIT', page.extract_text())
                    for char in page.chars:
                        self.assertGreaterEqual(char['x0'], 47.9)
                        self.assertLessEqual(char['x1'], 564.1)
                        self.assertGreaterEqual(char['top'], 40)
                        self.assertLessEqual(char['bottom'], 755)
            self.assertEqual(data, original)

    def test_every_rendered_continuation_has_only_actual_parties_initials(self):
        for code in (1953, 1954):
            for buyers in (1, 2):
                for sellers in (1, 2):
                    with self.subTest(code=code, buyers=buyers, sellers=sellers):
                        data = sample(code, long=True, buyers=buyers, sellers=sellers)
                        signing = {**data, '_for_signing': True}
                        fields = self.fields(code, signing)
                        self.assertEqual(fields, self.fields(code, data))
                        self.assertEqual(len({f['api_id'] for f in fields}), len(fields))
                        with pdfplumber.open(BytesIO(self.render(code, signing))) as pdf:
                            self.assertEqual(max(f['page'] for f in fields), len(pdf.pages))
                            for page in range(2, len(pdf.pages) + 1):
                                extra = [f for f in fields if f['page'] == page]
                                self.assertEqual({f['recipient_id'] for f in extra},
                                                 {str(i) for i in range(1, buyers + sellers + 1)})
                                self.assertTrue(all(f['required'] and f['type'] == 'initials' for f in extra))
                                for field in extra:
                                    left, top = field['x'] * .75, field['y'] * .75
                                    right, bottom = left + field['width'] * .75, top + field['height'] * .75
                                    self.assertLessEqual(bottom, 724)
                                    overlap = [c for c in pdf.pages[page-1].chars if c['x0'] < right and
                                               c['x1'] > left and c['top'] < bottom and c['bottom'] > top]
                                    self.assertEqual(overlap, [])

    def test_unicode_inline_names_and_inactive_answers(self):
        for code in (1953, 1954):
            data = {**sample(code), 'buyer_names': ['José 李']}
            text = PdfReader(BytesIO(self.render(code, data))).pages[0].extract_text()
            self.assertIn('José 李', text)
            data.update(lease_status='termination', delivery_choice='received',
                        oral_lease_notice='InactiveNotice', oral_fixture_lease_notice='InactiveNotice',
                        explanation='InactiveExplanation', leased_fixture_types=['solar_panels'],
                        leased_fixtures_other='InactiveOther', assumed_fixture_leases=['solar_panels'],
                        assumed_fixture_leases_other='InactiveAssumed')
            text = PdfReader(BytesIO(self.render(code, data))).pages[0].extract_text()
            self.assertNotIn('Inactive', text)
            self.assertEqual(len(self.fields(code, data)), 3)

    def test_actual_offline_render_send_preserves_pages_parties_and_parallel_signing(self):
        for code in (1953, 1954):
            for buyers, sellers in ((1, 1), (1, 2), (2, 1), (2, 2)):
                for long in (False, True):
                    with self.subTest(code=code, buyers=buyers, sellers=sellers, long=long):
                        # Reuse the real-delivery transport mock, replacing
                        # its representation fixture with a party addendum.
                        f = RenderSendFixture(self)
                        form = f'TXR-{code}'
                        data = sample(code, long=long, buyers=buyers, sellers=sellers)
                        data['signing_map_revision'] = MODULE.TXR_SIGNING_MAP_REVISIONS[form]
                        f.row.update(form_code=form, agreement_data=data,
                                     client_names=data['buyer_names'] + data['seller_names'])
                        f.source_bytes = blank_one_page_pdf()
                        f.emails = [f'party{i}@example.test' for i in range(buyers + sellers)]
                        f.recipients = MODULE._txr_signwell_recipients(f.row, f.emails, f.broker,
                            {'email': USER['email'], 'name': f.profile['agent_name']})
                        self.assertTrue(f.run()['ok'])
                        pdf = PdfReader(BytesIO(base64.b64decode(f.document['files'][0]['file_base64'])))
                        fields = f.document['fields'][0]
                        self.assertEqual(len(pdf.pages) > 1, long)
                        self.assertEqual(fields, self.fields(code, {**data, '_for_signing': True}))
                        self.assertEqual(f.document['recipients'], f.recipients)
                        self.assertEqual(len(f.recipients), buyers + sellers)
                        self.assertFalse(f.document['apply_signing_order'])
                        self.assertEqual(f.sends, 1)
                        self.assertEqual(f.downloads, 1)

    def test_fresh_render_uses_current_revisions_without_an_extra_preparation_gate(self):
        for code in (1953, 1954):
            form = f'TXR-{code}'
            self.assertEqual(MODULE.TXR_RENDER_REVISIONS[form], self.module(code).RENDER_REVISION)
            old = f'txr-{code}-2026-09-15-field-alignment-v2'
            current = MODULE._current_txr_signing_map_revision(form, {'signing_map_revision': old})
            self.assertEqual(current, MODULE.TXR_SIGNING_MAP_REVISIONS[form])
            self.assertNotEqual(current, old)

    def test_combined_packet_offsets_and_seller_ids_survive_both_continuations(self):
        configure_local_forms()
        for buyers, sellers in ((1, 1), (1, 2), (2, 1), (2, 2)):
            with self.subTest(buyers=buyers, sellers=sellers):
                offer = residential_lease_offer(
                    residentialLeaseDelivery='oral_notice', residentialLeaseOralNotice='O' * 500,
                    residentialLeaseExplanation='E' * 1200, leaseFixture='yes',
                    leasedFixtureTypes=['other'], leasedFixturesOther='F' * 180,
                    assumedFixtureLeases=['other'], assumedFixtureLeasesOther='L' * 180,
                    fixtureBuyerFirstCost='2500.75', fixtureRemovalChoice='will_not',
                    fixtureLeaseDelivery='oral_notice', fixtureLeaseOralNotice='N' * 500,
                    _paragraph4_source_pdf_bytes={f'TXR-{c}': blank_one_page_pdf() for c in (1953, 1954)},
                    uploadedDisclosureDocs=[{'name': 'QA.pdf', 'base64': one_page_pdf_base64(),
                        'signaturePlacements': [{'type': 'buyer1_signature', 'page': 1,
                                                 'signwellX': 50, 'signwellY': 50}]}])
                if buyers == 2:
                    offer.update(buyer2='Second Buyer', buyer2Email='two@example.test')
                if sellers == 2:
                    offer.update(paragraph4Seller2Name='Second Seller', paragraph4Seller2Email='seller2@example.test')
                packet = adapter.fill_and_merge_20_19(offer)
                pdf = PdfReader(BytesIO(packet))
                fields = adapter.build_signwell_fields_20_19(offer, packet)[0]
                cursor = 13
                parties = {'1', '3'} | ({'2'} if buyers == 2 else set()) | ({'4'} if sellers == 2 else set())
                for code in (1953, 1954):
                    data = adapter._paragraph4_render_data(offer, f'TXR-{code}')
                    pages = len(PdfReader(BytesIO(self.render(code, data))).pages)
                    self.assertGreater(pages, 1)
                    selected = [f for f in fields if f['api_id'].startswith(f'txr{code}')]
                    self.assertEqual({f['page'] for f in selected}, set(range(cursor, cursor + pages)))
                    for page in range(cursor, cursor + pages):
                        page_fields = [f for f in selected if f['page'] == page]
                        self.assertEqual({f['recipient_id'] for f in page_fields}, parties)
                        self.assertTrue(all(f['type'] == ('signature' if page == cursor else 'initials') for f in page_fields))
                    self.assertEqual(offer['_signing_render_revisions'][f'TXR-{code}'], self.module(code).RENDER_REVISION)
                    cursor += pages
                self.assertEqual(len(pdf.pages), cursor)
                self.assertEqual({f['page'] for f in fields if f['api_id'].startswith('uploaded_')}, {cursor})
                self.assertEqual(len({f['api_id'] for f in fields}), len(fields))


if __name__ == '__main__':
    unittest.main()
