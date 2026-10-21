"""Actual lease PDF composition, distinct source semantics and signer remapping."""
from copy import deepcopy
from io import BytesIO
import os
from pathlib import Path
import unittest

from pypdf import PdfReader

from lib import listing_packet as packet
from lib import txr_1102
from tests.test_txr_1102 import sample,BROKER,ASSOCIATE
from tests.test_listing_packet import pdf,signing_fields,component


class LeaseListingPacketTests(unittest.TestCase):
    def build(self,answers=None,documents=(),**changes):
        return packet.assemble_lease_listing_packet(answers or sample(),
            changes.pop('listing_pdf',pdf('Fictional lease listing',11)),
            changes.pop('listing_fields',signing_fields()),documents=documents,**changes)

    def test_requested_missing_documents_do_not_stop_the_listing_or_claim_inclusion(self):
        result=self.build()
        self.assertEqual(len(PdfReader(BytesIO(result.pdf)).pages),11)
        self.assertEqual(result.manifest['revision'],'lease-listing-packet-composition-v1')
        self.assertEqual([row['code'] for row in result.manifest['included']],['TXR-1102'])
        self.assertEqual([row['label'] for row in result.manifest['pending']],
            ['Information About Brokerage Services','Rental flood disclosure','Lead-based paint disclosure for a lease',
             'Assistance-animal information for landlords'])
        self.assertTrue(result.manifest['has_pending_documents'])
        self.assertNotIn('seller_disclosure',result.manifest)

    def test_always_requested_flood_and_age_based_lead_are_not_guessed_landlord_facts(self):
        for age,expected in [('yes',['B','C']),('unanswered',['B','C']),('no',['B'])]:
            result=self.build(sample(addenda=[],built_before_1978=age))
            self.assertEqual([row['code'] for row in result.manifest['pending']],expected)
            self.assertEqual([row['code'] for row in result.manifest['included']],['TXR-1102'])

    def test_correct_lease_order_actual_pages_offsets_and_namespace(self):
        answers=sample(addenda=['A','B','C'],built_before_1978='yes')
        docs=[component('C',pdf=pdf('Fictional rental lead',2)),
              component('A',pdf=pdf('Fictional saved IABS'),fields=[],recipient_map={}),
              component('B',pdf=pdf('Fictional rental flood'))]
        before=deepcopy(answers)
        result=self.build(answers,docs)
        self.assertEqual(answers,before)
        reader=PdfReader(BytesIO(result.pdf));self.assertEqual(len(reader.pages),15)
        self.assertIn('saved IABS',reader.pages[11].extract_text())
        self.assertIn('rental flood',reader.pages[12].extract_text())
        self.assertIn('rental lead',reader.pages[13].extract_text())
        self.assertEqual([(row['code'],row['start_page'],row['end_page']) for row in result.manifest['included']],
                         [('TXR-1102',1,11),('A',12,12),('B',13,13),('C',14,15)])
        self.assertEqual([f['page'] for f in result.fields[0]],[1,13,14])
        self.assertEqual([f['api_id'] for f in result.fields[0]],
                         ['seller_signature','listing_B_seller_signature','listing_C_seller_signature'])
        self.assertEqual(result.manifest['pending'],[])

    def test_landlord_field_ids_remap_explicitly_without_adding_tenant_or_unauthorized_signers(self):
        doc=component('B',fields=signing_fields('local-landlord'),recipient_map={'local-landlord':'2'})
        result=self.build(documents=[doc])
        self.assertEqual(result.fields[0][-1]['recipient_id'],'2')
        for target in ['tenant','buyer','seller','3']:
            with self.subTest(target=target),self.assertRaises(ValueError):
                self.build(documents=[component('B',recipient_map={'1':target})])
        with self.assertRaises(ValueError):
            self.build(sample(client_names=['QA Landlord']),documents=[doc])

    def test_sale_disclosure_binding_cannot_be_carried_into_rental_flood_slot(self):
        with self.assertRaisesRegex(ValueError,'lease-specific'):
            self.build(documents=[component('B',disclosure_binding={'id':'sale-disclosure'})])
        with self.assertRaises(ValueError):self.build(documents=[component('P')])

    def test_duplicate_unselected_invalid_pages_or_conflicting_fields_fail_visibly(self):
        for documents in ([component('B'),component('B')],[component('F')],
                          [component('B',fields=signing_fields(page=2))],
                          [component('B',pdf=b'not a PDF')],
                          [component('B',content_fingerprint='unverified')]):
            with self.subTest(documents=documents),self.assertRaises(ValueError):self.build(documents=documents)

    def test_optional_files_are_truly_missing_not_error_suppressed(self):
        result=self.build(pending_reasons={'B':'Landlord completion to follow.'})
        self.assertEqual(next(row for row in result.manifest['pending'] if row['code']=='B')['reason'],
                         'Landlord completion to follow.')
        with self.assertRaises(ValueError):self.build(documents=[component('A',pdf=b'%PDF-malformed')])

    def test_content_binding_is_stable_but_changes_with_actual_documents_or_legal_answers(self):
        listing=pdf('Stable fixture lease',11)
        original=self.build(listing_pdf=listing)
        signing=self.build(sample(_for_signing=True),listing_pdf=listing)
        self.assertEqual(original.content_fingerprint,signing.content_fingerprint)
        included=self.build(documents=[component('A',fields=[],recipient_map={})],listing_pdf=listing)
        self.assertNotEqual(original.content_fingerprint,included.content_fingerprint)
        changed=self.build(sample(listing_price='2600'),listing_pdf=listing)
        self.assertNotEqual(original.content_fingerprint,changed.content_fingerprint)

    @unittest.skipUnless(os.environ.get('HOF_TXR1102_SOURCE'),'Exact private lease source is opt-in.')
    def test_actual_source_continuations_and_single_broker_stay_before_appended_iabs(self):
        source=Path(os.environ['HOF_TXR1102_SOURCE']).read_bytes()
        for count,plan in [(1,'clients_and_broker'),(2,'clients_and_associate')]:
            answers=sample(client_names=['QA Landlord One','QA Landlord Two'][:count],signer_plan=plan,
                           special_provisions='Fictional résumé 李 continuation. '*120)
            listing=txr_1102.render_txr_1102(source,answers,BROKER,ASSOCIATE)
            pages=len(PdfReader(BytesIO(listing)).pages)
            fields=txr_1102.build_signwell_fields_txr1102(answers,client_count=count,page_count=pages)
            result=self.build(answers,[component('A',fields=[],recipient_map={})],listing_pdf=listing,listing_fields=fields)
            reader=PdfReader(BytesIO(result.pdf))
            self.assertGreater(pages,11);self.assertEqual(len(reader.pages),pages+1)
            self.assertEqual(result.manifest['included'][1]['start_page'],pages+1)
            self.assertIn('Fictional A',reader.pages[-1].extract_text())
            self.assertLessEqual(max(f['page'] for f in result.fields[0]),pages)
            self.assertEqual({f['recipient_id'] for f in result.fields[0]},
                             {'1','broker'} if count==1 else {'1','2','associate'})


if __name__=='__main__':unittest.main()
