"""Local-only ordinary listing specimen and bounded changed-page review images."""
import argparse
import json
from pathlib import Path
import pypdfium2 as pdfium
from lib import listing_package_signing_qa as qa
from scripts.qa.check_seller_disclosure_explanations import show_qa_fields


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args();args.output_dir.mkdir(parents=True,exist_ok=True)
    packet,fields,manifest=qa.build_packet(args.source.read_bytes())
    (args.output_dir/'ordinary-listing-unsigned.pdf').write_bytes(packet)
    guide=show_qa_fields(packet,fields[0])
    (args.output_dir/'ordinary-listing-placement-guide.pdf').write_bytes(guide)
    review=[1,2,9,10,11,12]
    document=pdfium.PdfDocument(guide)
    for number in review:
        page=document[number-1];bitmap=page.render(scale=1.35)
        bitmap.to_pil().save(args.output_dir/f'page-{number:02}.png')
        bitmap.close();page.close()
    document.close()
    result={'cases':manifest,'fields':fields,'layout_sha256':qa.layout_fingerprint(packet,fields),
        'review_images':review,'nothing_sent':True}
    (args.output_dir/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({key:value for key,value in result.items() if key!='fields'}))


if __name__=='__main__':main()
