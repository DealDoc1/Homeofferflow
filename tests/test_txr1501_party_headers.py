"""Party identification on every continuation page, without source PDFs."""
from io import BytesIO
import unittest
import pdfplumber
from pypdf import PdfWriter
from lib.txr_1501 import render_txr_1501


def render(clients, brokerage):
    source=BytesIO()
    writer=PdfWriter()
    for _ in range(6):writer.add_blank_page(width=612,height=792)
    writer.write(source)
    return render_txr_1501(source.getvalue(),{'client_names':clients,
        'signer_plan':'clients_and_associate'},brokerage,{'name':'QA Associate'})


class Txr1501PartyHeaderTests(unittest.TestCase):
    def assert_headers(self, raw, expected):
        with pdfplumber.open(BytesIO(raw)) as pdf:
            self.assertGreaterEqual(len(pdf.pages),6)
            self.assertFalse([c for c in pdf.pages[0].chars if c['top']<48])
            for number,page in enumerate(pdf.pages[1:6],2):
                chars=[c for c in page.chars if c['top']<48]
                with self.subTest(page=number):
                    self.assertEqual(''.join(c['text'] for c in chars),expected)
                    self.assertGreaterEqual(min(c['x0'] for c in chars),244.13)
                    self.assertLessEqual(max(c['x1'] for c in chars),576.10)
                    self.assertGreaterEqual(min(c['top'] for c in chars),30)
                    self.assertLessEqual(max(c['bottom'] for c in chars),42.48)
                    self.assertTrue(all(c['size']>=7 for c in chars))

    def test_one_and_two_clients_plus_brokerage_on_every_continuation_page(self):
        for clients in (['QA Client One'],['QA Client One','QA Client Two']):
            self.assert_headers(render(clients,{'legal_name':'QA Brokerage'}),
                                ', '.join(clients)+' and QA Brokerage')

    def test_existing_broker_name_fallbacks_and_whitespace_are_preserved(self):
        for key in ('name','dba_name'):
            self.assert_headers(render([' QA   Client '],{key:' QA   Brokerage '}),
                                'QA Client and QA Brokerage')

    def test_long_names_reference_full_party_block_instead_of_clipping(self):
        self.assert_headers(render(['Long Client Name '*12,'Another Long Name '*12],
                                   {'legal_name':'Long Brokerage Name '*12}),
                            'Client(s) and Broker identified in Paragraph 1')

    def test_headers_do_not_replace_full_names_in_primary_party_block(self):
        clients=['Long Client Name '*12]
        broker='Long Brokerage Name '*12
        with pdfplumber.open(BytesIO(render(clients,{'legal_name':broker}))) as pdf:
            first_page=' '.join(pdf.pages[0].extract_text().split())
            self.assertIn(' '.join(clients[0].split()),first_page)
            self.assertIn(' '.join(broker.split()),first_page)


if __name__=='__main__':unittest.main()
