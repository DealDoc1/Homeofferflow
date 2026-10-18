#!/usr/bin/env python3
"""Local fictional package specimens; the related page is not a real IABS."""
import argparse
import hashlib
from io import BytesIO
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pypdfium2
from pypdf import PdfReader
from reportlab.pdfgen.canvas import Canvas
from lib import txr_1101
from lib.listing_packet import PreparedDocument, assemble_listing_packet
from tests.test_txr_1101 import sample_answers, BROKER, ASSOCIATE
from scripts.render_txr1101_placement_qa import placement_guide


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',required=True,type=Path)
    parser.add_argument('--output-dir',required=True,type=Path)
    args=parser.parse_args();source=args.source.read_bytes()
    pdf_dir=args.output_dir/'output'/'pdf';image_dir=args.output_dir/'tmp'/'pdfs'
    pdf_dir.mkdir(parents=True,exist_ok=True);image_dir.mkdir(parents=True,exist_ok=True)
    stream=BytesIO();canvas=Canvas(stream,pagesize=(612,792))
    canvas.setFont('Helvetica-Bold',16);canvas.drawString(40,735,'TEST ONLY - FICTIONAL RELATED DOCUMENT')
    canvas.setFont('Helvetica',11);canvas.drawString(40,705,'This page substitutes for an agent-owned saved IABS in local QA.')
    canvas.drawString(40,685,'It is not a real IABS, a disclosure or a customer agreement.')
    canvas.drawString(40,655,'No seller, buyer or broker signing fields should appear on this page.')
    canvas.showPage();canvas.save();related=stream.getvalue()
    component=PreparedDocument('A',related,[],{},hashlib.sha256(related).hexdigest())
    cases={'standard-two':sample_answers(),
           'single-unicode':sample_answers(client_names=['QA José 李 Seller']),
           'continuation-two':sample_answers(special_provisions='QA Büro 李 '*240)}
    manifest=[]
    for name,answers in cases.items():
        primary=txr_1101.render_txr_1101(source,answers,BROKER,ASSOCIATE)
        primary_count=len(PdfReader(BytesIO(primary)).pages)
        fields=txr_1101.build_signwell_fields_txr1101(answers,client_count=len(answers['client_names']),page_count=primary_count)
        result=assemble_listing_packet(answers,primary,fields,documents=[component])
        guide=placement_guide(result.pdf,result.fields[0])
        output=pdf_dir/f'txr1101-packet-{name}.pdf';output.write_bytes(guide)
        rendered=pypdfium2.PdfDocument(guide);images=[]
        for number in (primary_count,primary_count+1):
            image=image_dir/f'{name}-p{number}.png'
            rendered[number-1].render(scale=1.5).to_pil().save(image);images.append(str(image))
        manifest.append({'case':name,'pdf':str(output),'images':images,'manifest':result.manifest,
                         'source_sha256':hashlib.sha256(source).hexdigest(),'completed_provider_verified':False})
    output=args.output_dir/'manifest.json';output.write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'cases':len(cases),'manifest':str(output),'pages':{row['case']:row['manifest']['page_count'] for row in manifest}},indent=2))


if __name__=='__main__':main()
