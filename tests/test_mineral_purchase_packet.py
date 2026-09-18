"""One purchase packet, private source, stable signers; no external calls."""
import base64
import copy
import hashlib
from io import BytesIO
import unittest
from unittest.mock import patch

import pdfplumber
from pypdf import PdfReader
from lib import production_adapter as adapter
from lib.offer_signwell_delivery import offer_answers
from tests.test_controlled_launch import configure_local_forms, minimal_offer, one_page_pdf_bytes, one_page_pdf_base64
from tests.test_paragraph4_source_hydration import load_offer_api, FakeResponse


def mineral_offer(**changes):
    return minimal_offer(mineralReservation='yes', mineralReservationChoice='undivided_interest',
        mineralUndividedInterest='25.125', mineralSurfaceRights='waived', seller1Name='Seller One',
        seller1Email='seller1@example.test', _paragraph4_source_pdf_bytes={'TXR-1905': one_page_pdf_bytes()}, **changes)


class MineralPacketTests(unittest.TestCase):
    def setUp(self):
        configure_local_forms()
        # CI uses an explicitly substituted blank fixture, not a checked-in
        # restricted source. Source-specific rendering is separately visual QA.
        self.hash = hashlib.sha256(one_page_pdf_bytes()).hexdigest()
        self.guard = patch.object(adapter, 'MINERAL_SOURCE_SHA256', self.hash)
        self.guard.start()
        self.addCleanup(self.guard.stop)

    def test_all_four_signer_counts_share_one_packet_and_correct_ids(self):
        for buyers in (1, 2):
            for sellers in (1, 2):
                with self.subTest(buyers=buyers, sellers=sellers):
                    offer = mineral_offer(**({'buyer2':'Buyer Two', 'buyer2Email':'two@example.test'} if buyers == 2 else {}),
                        **({'seller2Name':'Seller Two', 'seller2Email':'seller2@example.test'} if sellers == 2 else {}))
                    packet = adapter.fill_and_merge_20_19(offer)
                    fields = adapter.build_signwell_fields_20_19(offer, packet)[0]
                    mineral = [f for f in fields if f['api_id'].startswith('txr1905')]
                    self.assertEqual(len(PdfReader(BytesIO(packet)).pages), 13)
                    self.assertEqual({f['page'] for f in mineral}, {13})
                    self.assertEqual({f['recipient_id'] for f in mineral}, {'1', '3'} | ({'2'} if buyers == 2 else set()) | ({'4'} if sellers == 2 else set()))
                    self.assertEqual(len(mineral), buyers + sellers)
                    self.assertFalse(any(f['recipient_id'] in ('3', '4') and f['page'] <= 12 for f in fields))
                    self.assertIn(self.hash, offer['_signing_source_hashes'])
                    self.assertEqual(offer['_signing_render_revisions']['TXR-1905'], adapter.MINERAL_RENDER_REVISION)
                    text = PdfReader(BytesIO(packet)).pages[-1].extract_text()
                    self.assertIn('25.125%', text)
                    self.assertIn(offer['address'], text)
                    self.assertIn('TX', text)
                    self.assertNotIn('Seller One', text, 'Do not put draft names over signing blanks')

    def test_mineral_checkbox_is_inside_exact_paragraph22_cell(self):
        for selected in ('yes', 'no'):
            offer = mineral_offer()
            offer['mineralReservation'] = selected
            with pdfplumber.open(BytesIO(adapter.fill_and_merge_20_19(offer))) as pdf:
                marks = [c for c in pdf.pages[8].chars if c['text'] == 'X' and 61 <= c['x0'] <= 74 and 530 <= c['top'] <= 544]
                self.assertEqual(len(marks), int(selected == 'yes'))
                for mark in marks:
                    self.assertLessEqual(mark['x1'], 74)
                    self.assertLessEqual(mark['bottom'], 544)

    def test_mixed_packet_offsets_with_lease_hydrostatic_continuation_and_upload(self):
        offer = mineral_offer(leaseResidential='yes', leases='yes', residentialLeaseStatus='assignment',
            residentialLeaseDelivery='received', hydrostaticTesting='yes', hydrostaticRiskAllocation='seller',
            repairsText='repair ' * 500, asIs='repairs', buyer2='Buyer Two', buyer2Email='two@example.test',
            seller2Name='Seller Two', seller2Email='seller2@example.test',
            uploadedDisclosureDocs=[{'name':'QA.pdf', 'base64':one_page_pdf_base64(),
                'signaturePlacements':[{'type':'buyer1_signature', 'page':1, 'signwellX':50, 'signwellY':50}]}])
        offer['_paragraph4_source_pdf_bytes']['TXR-1953'] = one_page_pdf_bytes()
        packet = adapter.fill_and_merge_20_19(offer)
        fields = adapter.build_signwell_fields_20_19(offer, packet)[0]
        last = len(PdfReader(BytesIO(packet)).pages)
        for prefix, page in [('txr1953', last-3), ('trec48_1', last-2), ('txr1905', last-1), ('uploaded_', last)]:
            self.assertEqual({f['page'] for f in fields if f['api_id'].startswith(prefix)}, {page})
        self.assertEqual(len({f['api_id'] for f in fields}), len(fields))
        self.assertTrue(any(f['api_id'].startswith('repair_continuation') and f['recipient_id'] == '4' for f in fields))
        without = copy.deepcopy(offer)
        without['mineralReservation'] = 'no'
        old = adapter.build_signwell_fields_20_19(without, adapter.fill_and_merge_20_19(without))[0]
        self.assertEqual([f for f in fields if not f['api_id'].startswith(('txr1905', 'uploaded_'))],
                         [f for f in old if not f['api_id'].startswith('uploaded_')])

    def test_overflow_continuation_remaps_one_buyer_two_sellers_without_collision(self):
        offer = mineral_offer(address='LongStreet' * 55, seller2Name='Seller Two', seller2Email='two@example.test')
        packet = adapter.fill_and_merge_20_19(offer)
        fields = adapter.build_signwell_fields_20_19(offer, packet)[0]
        mineral = [f for f in fields if f['api_id'].startswith('txr1905')]
        self.assertEqual({f['page'] for f in mineral}, {13, 14})
        self.assertEqual({f['recipient_id'] for f in mineral if f['page'] == 14}, {'1', '3', '4'})
        self.assertIn(offer['address'], PdfReader(BytesIO(packet)).pages[-1].extract_text().replace('\n', ''))

    def test_terms_and_identities_rejected_before_any_pdf_render(self):
        for changes in ({'mineralReservationChoice':''}, {'mineralSurfaceRights':''},
                        *({'mineralUndividedInterest':v} for v in ('', '0', '-1', '101', 'NaN', '1e2', '1.12345')),
                        {'seller1Email':'bad'}, {'seller1Email':'BUYER@example.com'}, {'buyer2':'Missing email'},
                        {'seller1Name':'', 'seller1Email':'', 'seller':'', 'seller2Name':'Two', 'seller2Email':'two@example.test'},
                        {'address':''}, {'city':''}):
            offer = mineral_offer()
            offer.update(changes)
            with self.subTest(changes=changes), patch.object(adapter.verified, 'fill_and_merge') as render:
                with self.assertRaises(adapter.UnsupportedOfferPathError):
                    adapter.fill_and_merge_20_19(offer)
                render.assert_not_called()

    def test_all_reservation_ignores_old_percentage_and_unselected_ignores_old_terms(self):
        offer = mineral_offer()
        offer.update(mineralReservationChoice='all', mineralUndividedInterest='invalid stale value')
        self.assertEqual(adapter._mineral_render_data(offer)['undivided_interest'], '')
        offer.update(mineralReservation='no', mineralReservationChoice='', seller1Email='')
        offer.pop('_paragraph4_source_pdf_bytes')
        self.assertEqual(len(PdfReader(BytesIO(adapter.fill_and_merge_20_19(offer))).pages), 12)
        self.assertNotIn('TXR-1905', offer['_signing_render_revisions'])

    def test_legacy_selection_alias_and_deselected_lease_parties(self):
        offer = mineral_offer(paragraph4Seller1Name='Old', paragraph4Seller1Email='old@example.test')
        offer['mineralReservation'] = 'no'
        offer['mineralReservationAddendum'] = True
        self.assertEqual(adapter.mineral_execution_parties(offer)[0]['email'], 'seller1@example.test')
        self.assertEqual(len(PdfReader(BytesIO(adapter.fill_and_merge_20_19(offer))).pages), 13)

    def test_missing_or_changed_source_cannot_be_used_with_calibrated_map(self):
        for source in (None, {}, {'TXR-1905':'not bytes'}, {'TXR-1905':one_page_pdf_bytes()+b'changed'}):
            offer = mineral_offer()
            offer['_paragraph4_source_pdf_bytes'] = source
            with self.assertRaises(adapter.UnsupportedOfferPathError):
                adapter.fill_and_merge_20_19(offer)

    def test_combined_signwell_payload_is_one_file_with_simultaneous_recipients(self):
        api = load_offer_api()
        api.SIGNWELL_ENABLED = True
        api.SIGNWELL_API_KEY = 'fixture'
        offer = mineral_offer()
        packet = adapter.fill_and_merge_20_19(offer)
        captured = {}
        def deliver(record, payload, offer, **kwargs):
            captured.update(payload)
            return {'document_id':'fixture', 'document':{'status':'sent'}, 'state':'sent', 'message':'sent', 'recovered':False}
        with patch.object(api, 'deliver_offer_document', side_effect=deliver):
            result = api.create_signwell_signature_request(offer, packet)
        self.assertTrue(result['ok'])
        self.assertFalse(captured['apply_signing_order'])
        self.assertEqual([r['id'] for r in captured['recipients']], ['1', '3'])
        self.assertEqual(len(captured['files']), 1)
        self.assertEqual(base64.b64decode(captured['files'][0]['file_base64']), packet)
        self.assertIn('mineral-reservation addendum', captured['message'])
        self.assertNotIn('seller-side changes are handled separately', captured['message'])
        self.assertNotIn('_paragraph4_source_pdf_bytes', offer_answers(offer))

    def test_private_source_lookup_selects_mineral_without_brokerage_seat(self):
        api = load_offer_api()
        api.SUPABASE_URL, api.SUPABASE_SERVICE_ROLE_KEY = 'https://example.supabase.co', 'fixture'
        offer = mineral_offer()
        offer.pop('_paragraph4_source_pdf_bytes')
        with patch.object(api.httpx, 'get', side_effect=[
            FakeResponse(200, payload=[{'source_revision':'11-07-2022', 'storage_bucket':'private', 'storage_path':'TXR1905.pdf'}]),
            FakeResponse(200, content=one_page_pdf_bytes())]) as get:
            api.hydrate_paragraph4_sources(offer)
        self.assertEqual(get.call_args_list[0].kwargs['params']['form_code'], 'eq.TXR-1905')
        self.assertNotIn('brokerage_id', get.call_args_list[0].kwargs['params'])
        self.assertEqual(offer['paragraph4SourceRevisions'], {'TXR-1905':'11-07-2022'})
        self.assertTrue(offer['_paragraph4_source_pdf_bytes']['TXR-1905'].startswith(b'%PDF'))
        with patch.object(api.httpx, 'get') as get:
            api.hydrate_paragraph4_sources(offer)
            get.assert_not_called()


if __name__ == '__main__':
    unittest.main()
