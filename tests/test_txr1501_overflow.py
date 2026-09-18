"""Lossless answers and matching signing fields for long representation inputs."""
from io import BytesIO
import unittest
import pdfplumber
from pypdf import PdfReader
from lib.txr_1501 import render_txr_1501, _overlay, build_signwell_fields_txr1501
from lib.txr1501_answers import answer_layout
from tests.test_txr_1501_renderer import blank_six_page_pdf, sample_data
from tests.test_txr_signing_request_path import MODULE


class Txr1501OverflowTests(unittest.TestCase):
    def test_ordinary_answers_remain_six_pages(self):
        self.assertEqual(len(PdfReader(BytesIO(render_txr_1501(blank_six_page_pdf(),sample_data(),
            {'legal_name':'QA Brokerage'},{'name':'QA Associate'}))).pages),6)

    def test_long_answers_are_retained_and_every_added_page_is_initialed(self):
        for role in ('broker','associate'):
            for count in (1,2):
                data={**sample_data(),'client_names':['FirstName'+'X'*170,'SecondName'+'Y'*169][:count],
                      'market_area':'MarketArea'+'M'*790,'client_address':'Address'+'A'*293,
                      'client_email':'contact'+'z'*145+'@example.test',
                      'payment_county':'County'+'C'*94,'signer_plan':'clients_and_'+role}
                broker={'legal_name':'Brokerage'+'B'*170}
                raw=render_txr_1501(blank_six_page_pdf(),data,broker,{'name':'Associate'+'D'*170})
                reader=PdfReader(BytesIO(raw));self.assertGreater(len(reader.pages),6)
                with pdfplumber.open(BytesIO(raw)) as measured:
                    # Exclude repeated page headers/footers when an answer
                    # crosses a continuation-page boundary.
                    text=''.join(''.join((p.crop((48,106,564,680)).extract_text() or '').split())
                                 for p in measured.pages[6:])
                _,overflow=answer_layout(data,broker,{'name':'Associate'+'D'*170})
                for answer in overflow.values():self.assertIn(''.join(answer.split()),text)
                self.assertIn('Answer continuation (attached)',reader.pages[4].extract_text())
                fields=MODULE._txr_signwell_fields('TXR-1501',{**data,'page_count':999},count,rendered_pdf=raw)[0]
                expected={'1',role} if count==1 else {'1','2',role}
                for page in range(7,len(reader.pages)+1):
                    actual=[f for f in fields if f['page']==page]
                    self.assertEqual({f['recipient_id'] for f in actual},expected)
                    self.assertTrue(all(f['required'] and f['type']=='initials' for f in actual))
                self.assertEqual(max(f['page'] for f in fields),len(reader.pages))

    def test_long_values_do_not_escape_source_blanks(self):
        data={**sample_data(),'client_names':['Long Name '*100],
              'market_area':'W'*800,'client_email':'e'*165+'@example.test','payment_county':'C'*100}
        with pdfplumber.open(BytesIO(_overlay(data,{'legal_name':'Broker '*100},{}))) as pdf:
            for page in pdf.pages:
                self.assertTrue(all(c['size']>=7 for c in page.chars))
                self.assertTrue(all(35<=c['x0']<c['x1']<=576.1 for c in page.chars))
            self.assertIn('See exhibit',pdf.pages[0].extract_text())
            self.assertIn('Answer continuation (attached)',pdf.pages[4].extract_text())

    def test_markup_and_unicode_are_literal_not_reinterpreted(self):
        name='José <b>Buyer</b> & 李'
        data={**sample_data(),'client_names':[name],'market_area':('Literal <b>area</b> & district '*30)}
        raw=render_txr_1501(blank_six_page_pdf(),data,{'legal_name':'QA Brokerage'},{})
        text=' '.join(' '.join(p.extract_text().split()) for p in PdfReader(BytesIO(raw)).pages)
        self.assertIn(name,text)
        self.assertIn('Literal <b>area</b> & district',text)

    def test_invalid_rendered_page_count_is_rejected(self):
        for count in (0,5,True,6.5):
            with self.subTest(count=count),self.assertRaises(ValueError):
                build_signwell_fields_txr1501({'signer_plan':'clients_and_associate'},page_count=count)


if __name__=='__main__':unittest.main()
