"""Actual source/API packet composition with fictional data and blocked network."""
import argparse
import asyncio
import importlib.util
from io import BytesIO
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx
from pypdf import PdfReader
from lib.seller_disclosure_explanations import RENDER_REVISION
from lib.seller_questionnaire import required_answers
from lib.txr_1101 import render_txr_1101
from scripts.qa.check_seller_disclosure_explanations import show_qa_fields
from tests.test_txr_1101 import sample_answers, BROKER, ASSOCIATE

ROOT=Path(__file__).resolve().parents[2]
SPEC=importlib.util.spec_from_file_location('listing_disclosure_fixture_api',ROOT/'api/admin-dashboard.py')
API=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(API)
USER={'id':'11111111-1111-4111-8111-111111111111'}
DRAFT='22222222-2222-4222-8222-222222222222'
VERSION='44444444-4444-4444-8444-444444444444'
MAIN='55555555-5555-4555-8555-555555555555'
WATER='66666666-6666-4666-8666-666666666666'
REAL_CLIENT=httpx.AsyncClient


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--listing-source',type=Path,required=True)
    parser.add_argument('--disclosure-source',type=Path,required=True)
    parser.add_argument('--water-source',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args();args.output_dir.mkdir(parents=True,exist_ok=True)
    sources={MAIN:args.disclosure_source.read_bytes(),WATER:args.water_source.read_bytes()}
    cases=[]
    for label,names,water,long in [('one-seller',['QA Seller One'],False,False),
        ('two-sellers-water',['QA Seller One','QA Seller Two'],True,False),
        ('unicode-continuation',['Élodie 李 QA','Wei QA'],True,True)]:
        answers=sample_answers(client_names=names,property_address='QA ONLY - 100 Fictional Example Lane, Frisco, TX',
            addenda=['B','P'] if water else ['B'],disclosure_draft_id=DRAFT)
        keys,water_keys=required_answers(water)
        responses=dict.fromkeys(keys,'N');responses.update(seller_occupancy='Y',working_smoke_detectors='Y',roof_type='Composition',roof_age='8 years')
        well=dict.fromkeys(water_keys,'N')
        if long:
            responses['defect_roof']='Y'
            responses['known_defects_explanation']=('QA ONLY - Élodie reviewed the façade; 张伟 noted <paint> & trim. '*32).strip()
            well.update(water_wells_known='Y',well_ownership='other',water_well_count_total='1',water_well_count_in_use='1',water_well_count_capped='0',
                        well_agreement=('QA ONLY - José reviewed a shared well with Zoë. '*34).strip())
        row={'id':DRAFT,'agent_user_id':USER['id'],'brokerage_id':'77777777-7777-4777-8777-777777777777',
             'property_address':answers['property_address'],'seller_names':names,'buyer_names':[],
             'disclosure_source_id':MAIN,'water_source_id':WATER if water else None,
             'disclosure_source_revision':'05-04-2026','water_source_revision':'05-04-2026' if water else None,
             'review_content_revision':VERSION,'seller_review_render_revision':RENDER_REVISION,
             'seller_review_attested':True,'status':'draft','response_data':responses,'water_rights_data':well}
        async def get(path):
            if path.startswith('hof_seller_disclosure_drafts?'):return [row]
            if path.startswith('hof_seller_disclosure_review_links?'):
                return [{'seller_index':i,'seller_name':n,'seller_attested_name':n,'seller_attested_at':'2026-10-18T12:00:00Z',
                         'review_content_revision':VERSION,'review_render_revision':RENDER_REVISION} for i,n in enumerate(names,1)]
            if path.startswith('hof_brokerage_form_sources?'):
                source=MAIN if 'id=eq.'+MAIN in path else WATER
                return [{'id':source,'source_revision':'05-04-2026','storage_bucket':'fictional-sources','storage_path':source+'.pdf'}]
            raise AssertionError('Unexpected fixture read')
        def transport(request):
            if request.url.host!='fixture.supabase.test' or request.method!='GET' or not request.url.path.startswith('/storage/'):
                raise AssertionError('No network write, provider request or real connection is permitted')
            source=MAIN if MAIN in request.url.path else WATER
            return httpx.Response(200,content=sources[source])
        listing=render_txr_1101(args.listing_source.read_bytes(),answers,BROKER,ASSOCIATE)
        with patch.object(API,'_get',get),patch.object(API,'SUPABASE_URL','https://fixture.supabase.test'), \
             patch.object(API.httpx,'AsyncClient',lambda **kw:REAL_CLIENT(transport=httpx.MockTransport(transport))):
            packet=asyncio.run(API._assemble_owned_listing_packet(USER,answers,listing))
        assert not packet.manifest['pending'],packet.manifest
        fields=packet.fields[0]
        output=args.output_dir/(label+'.pdf')
        output.write_bytes(show_qa_fields(packet.pdf,fields))
        cases.append({'case':label,'pages':len(PdfReader(BytesIO(packet.pdf)).pages),
                      'fields':fields,'manifest':packet.manifest,'nothing_sent':True})
    (args.output_dir/'manifest.json').write_text(json.dumps({'cases':cases,'nothing_sent':True},indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'nothing_sent':True,'cases':[{'case':r['case'],'pages':r['pages'],'fields':len(r['fields'])} for r in cases]}))


if __name__=='__main__':main()
