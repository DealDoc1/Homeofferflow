"""Local composition specimens only. No provider call, email or real signature."""
import argparse
import base64
from contextlib import redirect_stdout
import hashlib
from io import BytesIO, StringIO
import json
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from lib import production_adapter as adapter
from lib.seller_disclosure_explanations import RENDER_REVISION
from lib.trec_seller_disclosure import render_unsigned_preview
from tests.test_controlled_launch import configure_local_forms, minimal_offer


def prepare(main, water, out):
    configure_local_forms()
    out.mkdir(parents=True,exist_ok=True)
    for case, second, include_water in [('one-buyer',False,False),('two-buyers-water',True,True)]:
        writer=PdfWriter()
        source=render_unsigned_preview(main,'TREC-55-1',{'propertyAddress':'123 QA Road, Dallas, TX 75201'},qa_mode=True)
        writer.append(PdfReader(BytesIO(source)))
        if include_water:
            writer.append(PdfReader(BytesIO(render_unsigned_preview(water,'TREC-61-0',{'propertyAddress':'123 QA Road, Dallas, TX 75201'},qa_mode=True))))
        audit=BytesIO(); c=canvas.Canvas(audit,pagesize=(612,792))
        c.drawString(40,720,'LOCAL QA AUDIT PLACEHOLDER - NO SIGNATURES OR PROVIDER CLAIM');c.save()
        writer.append(PdfReader(BytesIO(audit.getvalue())))
        raw=BytesIO();writer.write(raw);raw=raw.getvalue()
        doc={'name':'Fictional-seller-disclosure.pdf','type':'seller_disclosure','base64':base64.b64encode(raw).decode(),
             'homeOfferFlowDisclosureReceipt':{'sourceDisclosureId':'fictional-qa','propertyAddress':'123 QA Road, Dallas, TX 75201',
                'sourceRevision':'05-04-2026','hasWaterRights':include_water,'renderRevision':RENDER_REVISION,'sha256':hashlib.sha256(raw).hexdigest()}}
        offer=minimal_offer(address='123 QA Road',city='Dallas',state='TX',zip='75201',buyer2='QA Buyer Two' if second else '',
            buyer2Email='qa-two@example.com' if second else '',uploadedDisclosureDocs=[doc])
        with redirect_stdout(StringIO()):
            pdf=adapter.fill_and_merge_20_19(offer)
            fields=adapter.build_signwell_fields_20_19(offer,pdf)[0]
        receipts=[f for f in fields if f['api_id'].startswith('saved_disclosure_')]
        # Pixels must be identical after appending; the composition never edits
        # the signed source, its existing marks, continuations or audit pages.
        import pypdfium2 as pdfium
        before,after=pdfium.PdfDocument(raw),pdfium.PdfDocument(pdf)
        offset=len(after)-len(before)
        for n in range(len(before)):
            assert before[n].render(scale=1).to_pil().tobytes()==after[offset+n].render(scale=1).to_pil().tobytes()
        reviewed=PdfWriter()
        for page_no,page in enumerate(PdfReader(BytesIO(pdf)).pages,start=1):
            marks=[f for f in receipts if f['page']==page_no]
            if marks:
                overlay=BytesIO();can=canvas.Canvas(overlay,pagesize=(612,792))
                can.setStrokeColorRGB(.1,.4,.8);can.setFillColorRGB(.1,.3,.6);can.setFont('Helvetica',7)
                for f in marks:
                    x,y,w,h=f['x']*.75,792-(f['y']+f['height'])*.75,f['width']*.75,f['height']*.75
                    can.rect(x,y,w,h);can.drawString(x+2,y+2,'QA BUYER '+f['recipient_id']+' '+f['type'])
                can.save();page.merge_page(PdfReader(BytesIO(overlay.getvalue())).pages[0])
            reviewed.add_page(page)
        target=out/(case+'-local-placement.pdf')
        with target.open('wb') as stream:reviewed.write(stream)
        rendered=pdfium.PdfDocument(target)
        for number in sorted({f['page'] for f in receipts}):
            rendered[number-1].render(scale=1.3).to_pil().save(out/(case+f'-page-{number}.png'))
        (out/(case+'-fields.json')).write_text(json.dumps(receipts,indent=2))
        print(case,{'pages':len(after),'buyerFields':len(receipts),'all_appended_page_pixels_identical':True})


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--main',type=Path,required=True);p.add_argument('--water',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    args=p.parse_args();prepare(args.main.read_bytes(),args.water.read_bytes(),args.out)
