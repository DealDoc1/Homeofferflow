"""Interview guidance must match the concurrent invitation policy."""
from html.parser import HTMLParser
from pathlib import Path
import unittest


class InterviewText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.targets = {'h-b2email': [], 'sellerTemporaryLeaseFields': []}
        self.stack = []

    def handle_starttag(self, tag, attrs):
        # Void elements do not have closing tags to balance the stack.
        if tag not in {'area', 'base', 'br', 'col', 'embed', 'hr', 'img',
                       'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}:
            self.stack.append((tag, dict(attrs).get('id')))

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                break

    def handle_data(self, data):
        for _, element_id in self.stack:
            if element_id in self.targets:
                self.targets[element_id].append(data)


class ConcurrentSigningInterviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        parser = InterviewText()
        parser.feed((Path(__file__).resolve().parents[1] / 'index.html').read_text())
        cls.text = {key: ' '.join(' '.join(parts).split())
                    for key, parts in parser.targets.items()}

    def test_cobuyer_can_sign_without_waiting_for_the_other_buyer(self):
        text = self.text['h-b2email']
        self.assertIn('Both buyers receive their own signing links at the same time', text)
        self.assertIn('can sign independently', text)

    def test_temporary_lease_explains_roles_without_sequential_delivery(self):
        text = self.text['sellerTemporaryLeaseFields']
        self.assertIn('Buyers sign as landlords; sellers sign as tenants.', text)
        self.assertIn('Everyone receives a signing link at the same time.', text)

    def test_neither_interview_instruction_tells_a_recipient_to_wait(self):
        for element_id, text in self.text.items():
            for stale in ('after you sign', 'landlords first', 'tenant afterward'):
                with self.subTest(element=element_id, phrase=stale):
                    self.assertNotIn(stale, text)
