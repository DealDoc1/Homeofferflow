#!/usr/bin/env python3
"""Render only the changed notice-contact pages using fictional data."""
import argparse
import hashlib
from io import BytesIO
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pypdf import PdfReader
import pypdfium2
from lib.txr_1101 import render_txr_1101, build_signwell_fields_txr1101, REVISION
from tests.test_txr_1101 import sample_answers, BROKER, ASSOCIATE
from scripts.render_txr1101_placement_qa import placement_guide


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',required=True,type=Path)
    parser.add_argument('--output-dir',required=True,type=Path)
    args=parser.parse_args();source=args.source.read_bytes()
    pdf_dir=args.output_dir/'output'/'pdf';images=args.output_dir/'tmp'/'pdfs'
    pdf_dir.mkdir(parents=True,exist_ok=True);images.mkdir(parents=True,exist_ok=True)
    cases={
        'independent':{'address':'42 Fictional Notice Lane','city_state_zip':'Plano, TX 75024',
                       'phone':'214-555-0123','email':'notices@example.test','email_2':''},
        'cleared':{},
        'unicode-overflow':{'address':('QA Büro 李 '*28).strip(),
                            'city_state_zip':'Québec, QC G1R 5M1',
                            'phone':'214-555-0123 ext. 42',
                            'email':'qa.'+'long-notice-'*11+'@example.test','email_2':''},
    }
    manifest=[]
    for name,contacts in cases.items():
        answers=sample_answers(broker_notice_contacts=contacts,
                               client_names=['QA José Seller'] if name=='cleared' else ['QA Seller One','QA Seller Two'])
        packet=render_txr_1101(source,answers,BROKER,ASSOCIATE)
        count=len(PdfReader(BytesIO(packet)).pages)
        fields=build_signwell_fields_txr1101(answers,client_count=len(answers['client_names']),page_count=count)[0]
        guide=placement_guide(packet,fields);pdf_path=pdf_dir/f'txr1101-notice-{name}.pdf';pdf_path.write_bytes(guide)
        rendered=pypdfium2.PdfDocument(guide);page_images=[]
        for number in [1]+([8] if count>10 else [])+list(range(11,count+1)):
            output=images/f'{name}-p{number}.png'
            rendered[number-1].render(scale=1.5).to_pil().save(output)
            page_images.append(str(output))
        manifest.append({'case':name,'pages':count,'pdf':str(pdf_path),'images':page_images,
                         'source_sha256':hashlib.sha256(source).hexdigest(),'render_revision':REVISION,
                         'completed_provider_verified':False})
    path=args.output_dir/'manifest.json';path.write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'manifest':str(path),'cases':len(manifest),'pages':{row['case']:row['pages'] for row in manifest}},indent=2))


if __name__=='__main__':main()
