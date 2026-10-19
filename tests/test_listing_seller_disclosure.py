"""Reviewed disclosure composition and ownership; never contacts a provider."""
import asyncio
from copy import deepcopy
from io import BytesIO
import unittest
from unittest.mock import AsyncMock, patch

from pypdf import PdfReader
from lib import listing_packet
from lib import listing_seller_disclosure as module
from lib.seller_questionnaire import required_answers
from lib.seller_disclosure_explanations import RENDER_REVISION
from tests.test_listing_packet import pdf, component, signing_fields
from tests.test_txr_1101 import sample_answers
from tests.test_seller_review_revision_binding import API, DRAFT, VERSION, OTHER_VERSION

USER={'id':DRAFT['agent_user_id']}


def disclosure(water=False,**changes):
    main, well=required_answers(water)
    row={**deepcopy(DRAFT),'property_address':sample_answers()['property_address'],
         'seller_names':sample_answers()['client_names'],'buyer_names':[],
         'response_data':dict.fromkeys(main,'N'),'water_rights_data':dict.fromkeys(well,'U'),
         'seller_review_render_revision':RENDER_REVISION,'status':'draft',
         'water_source_id':'33333333-3333-4333-8333-333333333333' if water else None,
         'disclosure_source_id':'66666666-6666-4666-8666-666666666666',
         'disclosure_source_revision':'05-04-2026','signwell_document_id':None}
    row['response_data']['working_smoke_detectors']='Y'
    row.update(changes);return row


class ListingSellerDisclosureTests(unittest.TestCase):
    def prepare(self,water=False,**changes):
        answers=sample_answers(addenda=['B','P'] if water else ['B'])
        row=disclosure(water,**changes)
        doc=module.prepare_reviewed_disclosure(answers,row,pdf('Fictional disclosure',7 if water else 5),
                                              {'source':'a'*64},{'continuation_pages':[7 if water else 5]})
        return answers,row,doc

    def test_one_seller_and_reversed_unicode_sellers_map_explicitly_without_extra_signers(self):
        answers=sample_answers(client_names=['Élodie 李','Wei QA'])
        row=disclosure(seller_names=['Wei QA','Élodie 李'])
        self.assertEqual(module.matching_sellers(answers,row),{'1':'2','2':'1'})
        self.assertEqual(module.matching_sellers({**answers,'client_names':['Élodie 李']},
            {**row,'seller_names':['Élodie 李']}),{'1':'1'})
        for change in ({'seller_names':['Other seller']},{'property_address':'Another house'},
                       {'buyer_names':['Another signer']},{'seller_names':['Wei QA','Wei QA']}):
            self.assertIsNone(module.matching_sellers(answers,{**row,**change}))

    def test_combined_water_and_continuations_merge_once_with_all_fields_remapped(self):
        answers,row,doc=self.prepare(True)
        result=listing_packet.assemble_listing_packet(answers,pdf('Fictional listing',10),signing_fields(),documents=[doc])
        self.assertEqual(len(PdfReader(BytesIO(result.pdf)).pages),17)
        self.assertEqual([(r['code'],r['start_page'],r['end_page']) for r in result.manifest['included']],
                         [('TXR-1101',1,10),('B',11,17),('P',15,16)])
        self.assertEqual(result.manifest['pending'],[])
        self.assertEqual(result.manifest['included'][-1]['included_with'],'B')
        fields=result.fields[0][1:]
        self.assertEqual({f['recipient_id'] for f in fields},{'1','2'})
        self.assertEqual({f['page'] for f in fields if f['type']=='signature'},{14,16})
        self.assertEqual({f['page'] for f in fields if f['type']=='initials'},{15,17})
        self.assertEqual(result.manifest['seller_disclosure']['revision'],VERSION)

    def test_main_disclosure_signature_and_continuation_follow_the_primary_packet(self):
        answers,row,doc=self.prepare()
        result=listing_packet.assemble_listing_packet(answers,pdf('Fictional listing',10),signing_fields(),documents=[doc])
        self.assertEqual(len(PdfReader(BytesIO(result.pdf)).pages),15)
        self.assertEqual({f['page'] for f in result.fields[0][1:]},{14,15})
        self.assertFalse(doc.contained_documents)

    def test_duplicate_water_and_invalid_contained_page_ranges_are_rejected(self):
        answers,row,doc=self.prepare(True)
        with self.assertRaises(ValueError):
            listing_packet.assemble_listing_packet(answers,pdf('Listing',10),signing_fields(),documents=[doc,component('P')])
        from dataclasses import replace
        for bounds in ((5,99),(0,2),('5',6),(6,5)):
            with self.subTest(bounds=bounds),self.assertRaises(ValueError):
                listing_packet.assemble_listing_packet(answers,pdf('Listing',10),signing_fields(),
                    documents=[replace(doc,contained_documents={'P':bounds})])

    def test_incomplete_answers_cannot_be_presented_as_an_included_disclosure(self):
        with self.assertRaises(ValueError): self.prepare(response_data={})

    def test_review_version_sources_and_answers_bind_the_packet_fingerprint(self):
        answers,row,doc=self.prepare()
        same=module.prepare_reviewed_disclosure(answers,row,pdf('Other PDF timestamp',5),{'source':'a'*64},{'continuation_pages':[5]})
        self.assertEqual(doc.content_fingerprint,same.content_fingerprint)
        changed=module.prepare_reviewed_disclosure(answers,{**row,'review_content_revision':OTHER_VERSION},doc.pdf,
                                                 {'source':'a'*64},{'continuation_pages':[5]})
        self.assertNotEqual(doc.content_fingerprint,changed.content_fingerprint)

    def test_owner_adapter_revalidates_current_review_and_expected_render_revision(self):
        row=disclosure(); answers=sample_answers(addenda=['B'],disclosure_draft_id=row['id'])
        get=AsyncMock(return_value=[row]);render=AsyncMock(return_value=pdf('Disclosure',4))
        with patch.object(API,'_get',get),patch.object(API,'_seller_reviews_complete_for_draft',AsyncMock(return_value=True)), \
             patch.object(API,'_render_seller_disclosure_draft_preview',render):
            doc,reason=asyncio.run(API._owned_listing_disclosure(USER,answers))
        self.assertIsNotNone(doc);self.assertIsNone(reason)
        self.assertIn('agent_user_id=eq.'+USER['id'],get.await_args.args[0])
        self.assertEqual(render.await_args.kwargs['expected_review_revision'],VERSION)

    def test_missing_stale_already_sent_or_other_packet_remains_pending_without_rendering(self):
        row=disclosure();answers=sample_answers(addenda=['B'],disclosure_draft_id=row['id'])
        for rows,review in (([],True),([{**row,'signwell_document_id':'sent'}],True),
                           ([{**row,'signature_packet_id':'other-packet'}],True),([row],False),
                           ([{**row,'seller_review_render_revision':'old'}],True)):
            render=AsyncMock()
            with patch.object(API,'_get',AsyncMock(return_value=rows)), \
                 patch.object(API,'_seller_reviews_complete_for_draft',AsyncMock(return_value=review)), \
                 patch.object(API,'_render_seller_disclosure_draft_preview',render):
                doc,reason=asyncio.run(API._owned_listing_disclosure(USER,answers))
            self.assertIsNone(doc);self.assertTrue(reason);render.assert_not_awaited()

    def test_wrong_owner_readback_is_rejected_and_changed_render_becomes_pending(self):
        row=disclosure();answers=sample_answers(addenda=['B'],disclosure_draft_id=row['id'])
        with patch.object(API,'_get',AsyncMock(return_value=[{**row,'agent_user_id':'another-owner'}])):
            with self.assertRaises(PermissionError): asyncio.run(API._owned_listing_disclosure(USER,answers))
        with patch.object(API,'_get',AsyncMock(return_value=[row])), \
             patch.object(API,'_seller_reviews_complete_for_draft',AsyncMock(return_value=True)), \
             patch.object(API,'_render_seller_disclosure_draft_preview',AsyncMock(side_effect=PermissionError('Changed'))):
            doc,reason=asyncio.run(API._owned_listing_disclosure(USER,answers))
        self.assertIsNone(doc);self.assertTrue(reason)


if __name__=='__main__':unittest.main()
