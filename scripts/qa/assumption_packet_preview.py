"""Local synthetic purchase/assumption PDFs; no provider or database calls."""
import argparse
import hashlib
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from lib.production_adapter import fill_and_merge_20_19, build_signwell_fields_20_19, ASSUMPTION_SOURCE_SHA256
from scripts.render_txr_signwell_map_review import _overlay
from tests.test_controlled_launch import configure_local_forms
from tests.test_assumption_purchase_packet import assumption_offer


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',required=True)
    parser.add_argument('--output-dir',required=True)
    args=parser.parse_args()
    source=Path(args.source).read_bytes()
    assert hashlib.sha256(source).hexdigest()==ASSUMPTION_SOURCE_SHA256
    reader=PdfReader(BytesIO(source))
    assert not reader.get_fields() and not any(ref.get_object().get('/Subtype')=='/Widget'
        for page in reader.pages for ref in page.get('/Annots',[]))
    configure_local_forms()
    target=Path(args.output_dir);target.mkdir(parents=True,exist_ok=True)
    cases={'both-loans':{'buyer2':'QA Buyer Two','buyer2Email':'buyer2@example.test',
                         'seller2Name':'QA Seller Two','seller2Email':'seller2@example.test'},
           'second-long':{'assumptionFirstEnabled':False,'assumptionSecondLender':'QA Long Lender Name '*22,
                          'assumptionVarianceAdjustment':'sales_price'}}
    for name,changes in cases.items():
        offer=assumption_offer(buyer1='QA Buyer One',buyerEmail='buyer1@example.test',seller='QA Seller One',
            address='100 QA ONLY Street',city='Frisco',zip='75034',
            _paragraph4_source_pdf_bytes={'TXR-1919':source},**changes)
        raw=fill_and_merge_20_19(offer)
        (target/(name+'.pdf')).write_bytes(raw)
        fields=[f for f in build_signwell_fields_20_19(offer,raw)[0] if f['api_id'].startswith('txr1919')]
        writer=PdfWriter()
        for number,page in enumerate(PdfReader(BytesIO(raw)).pages,1):
            if any(field['page']==number for field in fields):
                page.merge_page(PdfReader(BytesIO(_overlay(number,fields))).pages[0])
            writer.add_page(page)
        with (target/(name+'-map.pdf')).open('wb') as stream:writer.write(stream)
        print({'case':name,'pages':len(writer.pages),'loan':offer['loanAmount'],'cash':offer['downPayment'],
               'signing_fields':len(fields),'provider_contacted':False})


if __name__=='__main__':main()
