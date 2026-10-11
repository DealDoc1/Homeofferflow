from pathlib import Path
import subprocess
import unittest

from lib.brokerage_defaults import broker_license
from lib.trec_20_19_contacts import answer_layout as purchase_layout
from lib.txr1501_answers import answer_layout as long_layout
from lib.txr1507_answers import answer_layout as short_layout
from lib.txr1508_answers import answer_layout as showing_layout


class BrokerageLicenseDefaultTests(unittest.TestCase):
    def test_only_the_named_brokerage_receives_the_owner_confirmed_default(self):
        for name in ('OnDemand Realty', 'on demand realty', '  ONDEMAND REALTY  '):
            self.assertEqual(broker_license(name, '  '), '9010832')
        for name in ('Other Realty', 'OnDemand Realty Group', '', None):
            self.assertEqual(broker_license(name), '')

    def test_explicit_license_numbers_are_never_replaced(self):
        self.assertEqual(broker_license('OnDemand Realty', ' 1234567 '), '1234567')
        self.assertEqual(broker_license('Other Realty', '7654321'), '7654321')

    def test_purchase_default_is_in_the_broker_blank_not_the_associate_blank(self):
        entries = purchase_layout({'userType': 'agent', 'agentBrokerage': 'OnDemand Realty',
                                  'agentBrokerLicense': '', 'agentLicense': '1234567'}).pages[11]
        self.assertTrue(any(e[:3] == (179, 470, '9010832') for e in entries))
        self.assertTrue(any(e[:3] == (423, 412, '1234567') for e in entries))

    def test_each_representation_and_showing_license_blank_receives_the_default(self):
        for layout, page, x, y in ((long_layout, 6, 240, 400), (short_layout, 2, 240, 292),
                                  (showing_layout, None, 478, 316)):
            for key in ('legal_name', 'name', 'dba_name'):
                with self.subTest(layout=layout.__module__, key=key):
                    result, _ = layout({}, {key: 'OnDemand Realty', 'license_number': ''},
                                       {'name': 'QA Associate', 'license_number': '1234567'})
                    entries = result[page] if page else result
                    self.assertTrue(any(e[:3] == (x, y, '9010832') for e in entries))

    def test_browser_defaults_runtime(self):
        result = subprocess.run(['node', '--test', str(Path(__file__).with_name('brokerage_license_defaults.runtime.cjs'))],
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
