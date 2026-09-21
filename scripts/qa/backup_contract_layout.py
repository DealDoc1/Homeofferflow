"""Render private backup-contract QA specimens without sending documents."""
import argparse
from io import BytesIO
from pathlib import Path
import subprocess
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen.canvas import Canvas
from lib import production_adapter as adapter
from tests.test_controlled_launch import configure_local_forms
from tests.test_backup_contract_layout import sample


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output_dir',type=Path)
    args=parser.parse_args(); args.output_dir.mkdir(parents=True,exist_ok=True)
    configure_local_forms()
    cases={'ordinary':sample(),
           'zero-one-buyer':sample(buyer2Email='',bkupAdditionalEarnest=0,bkupAdditionalOption=0),
           'long':sample(address='José 李 <b>Property</b> & '+'Z'*400)}
    for label,offer in cases.items():
        raw=adapter.fill_and_merge_20_19(offer); reader=PdfReader(BytesIO(raw))
        fields=adapter.build_signwell_fields_20_19(offer,raw)[0]
        selected=sorted({f['page'] for f in fields if 'backup' in f['api_id']})
        writer=PdfWriter(); writer.append(reader,pages=[p-1 for p in selected])
        for i,number in enumerate(selected):
            out=BytesIO(); canvas=Canvas(out,pagesize=(612,792)); canvas.setFillColorRGB(.1,.25,.8)
            canvas.setFont('Helvetica',8)
            canvas.drawString(40,780,f'LOCAL QA ONLY - packet page {number} - boxes are NOT signatures')
            for field in fields:
                if field['page']!=number:continue
                x=field['x']*.75; y=792-(field['y']+field['height'])*.75
                canvas.setStrokeColorRGB(.1,.25,.8)
                canvas.rect(x,y,field['width']*.75,field['height']*.75)
                canvas.setFont('Helvetica',5 if field['type']=='initials' else 8)
                role='B' if field['type']=='initials' else 'Buyer '
                canvas.drawString(x+2,y+3,f"{role}{field['recipient_id']} {field['type']}")
            canvas.showPage(); canvas.save()
            writer.pages[i].merge_page(PdfReader(BytesIO(out.getvalue())).pages[0])
        path=args.output_dir/(label+'.pdf')
        with path.open('wb') as stream:writer.write(stream)
        subprocess.run(['pdftoppm','-scale-to','1400','-png',str(path),str(path.with_suffix(''))],check=True)
        print(label,selected)


if __name__=='__main__':main()
