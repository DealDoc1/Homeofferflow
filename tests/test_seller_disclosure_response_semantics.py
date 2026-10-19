"""Real renderer checks for the Y/N/U property-item lines, not signing QA."""
from io import BytesIO
import hashlib
import json
import unittest
from unittest.mock import patch

from pypdf import PdfReader
from reportlab.pdfgen.canvas import Canvas
from lib import trec_seller_disclosure as disclosure


class SellerDisclosureResponseSemanticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Test-only blank paper avoids packaging the licensed source artwork.
        stream = BytesIO()
        canvas = Canvas(stream, pagesize=(612, 792))
        for _ in range(4):
            canvas.showPage()
        canvas.save()
        cls.blank = stream.getvalue()

    def render(self, values):
        with patch.object(disclosure, "validate_source_bytes"):
            return disclosure.render_unsigned_preview(
                self.blank, "TREC-55-1", values, qa_mode=True)

    def test_no_and_unknown_are_letters_never_positive_checkmarks(self):
        for key in disclosure.TREC_55_1_FEATURE_RESPONSES:
            for value in ("Y", "N", "U"):
                with self.subTest(key=key, value=value), \
                     patch.object(disclosure, "_check") as checks:
                    result = self.render({key: value})
                    text = PdfReader(BytesIO(result)).pages[0].extract_text()
                    self.assertIn(value, text.split())
                    checks.assert_not_called()

    def test_false_legacy_booleans_are_not_lost(self):
        for value, expected in ((True, "Y"), (False, "N")):
            with self.subTest(value=value):
                text = PdfReader(BytesIO(self.render({"water_heater_gas": value}))).pages[0].extract_text()
                self.assertIn(expected, text.split())

    def test_empty_choice_stays_blank(self):
        for value in (None, ""):
            with self.subTest(value=value):
                text = PdfReader(BytesIO(self.render({"water_heater_gas": value}))).pages[0].extract_text()
                self.assertEqual(text.strip(), "")

    def test_canonical_choice_overrides_legacy_alias_at_same_line(self):
        anchor = disclosure.TREC_55_1_MAP["lp_community"]
        with patch.object(disclosure, "_response", wraps=disclosure._response) as responses:
            self.render({"lp_community": "N", "liquid_propane_lp_community": True})
            at_anchor = [call.args[1] for call in responses.call_args_list
                         if call.args[2:] == (anchor["x"], anchor["y"])]
        self.assertEqual(at_anchor, ["N"])

    def test_legacy_aliases_keep_their_no_and_unknown_values(self):
        for key in ("liquid_propane_lp_community", "liquid_propane_on_property",
                    "fuel_gas_corrugated_stainless", "garage_carport",
                    "garage_door_electronic", "garage_door_controls"):
            with self.subTest(key=key):
                text = PdfReader(BytesIO(self.render({key: "N"}))).pages[0].extract_text()
                self.assertIn("N", text.split())

    def test_letters_fit_the_independently_measured_source_response_lines(self):
        # Original 05-04-2026 source horizontal strokes (PDF bottom-left
        # coordinates), measured with pdfplumber. Not derived from our map.
        lines = {
            "water_heater_gas": (171.74, 199.17, 182.01),
            "water_heater_electric": (289.60, 318.85, 182.01),
            "water_supply_city": (171.74, 200.12, 163.58),
            "water_supply_well": (289.33, 318.99, 164.31),
            "water_supply_mud": (404.66, 430.88, 163.10),
            "water_supply_coop": (509.70, 539.78, 163.36),
            "lp_community": (177.57, 206.57, 254.99),
            "lp_on_property": (312.38, 340.39, 254.99),
            "fuel_gas_black_iron": (160.10, 188.24, 236.54),
            "fuel_gas_corrugated_steel": (254.19, 282.44, 236.58),
            "fuel_gas_copper": (425.38, 452.52, 236.05),
            "garage_attached": (99.49, 127.74, 219.58),
            "garage_not_attached": (215.40, 244.43, 218.61),
            "carport": (341.48, 369.56, 218.61),
            "garage_opener_electronic": (171.27, 199.33, 200.70),
            "garage_opener_controls": (289.60, 318.21, 200.73),
            "hot_tub": (477.55, 505.04, 332.68),
        }
        self.assertEqual(set(lines), set(disclosure.TREC_55_1_FEATURE_RESPONSES))
        for key, (left, right, rule_y) in lines.items():
            with self.subTest(key=key):
                anchor = disclosure.TREC_55_1_MAP[key]
                self.assertGreater(anchor["x"], left)
                self.assertLess(anchor["x"] + 6, right)
                self.assertGreaterEqual(anchor["y"] - rule_y, 2)
                self.assertLessEqual(anchor["y"] - rule_y, 3)

    def test_new_execution_maps_preserve_unique_roles_for_all_party_counts(self):
        # Layout changes now have source-rule bounds tests; an old hash of
        # unverified geometry must not require preserving misplaced widgets.
        for code in ('TREC-55-1','TREC-61-0'):
            for sellers in (1,2):
                for buyers in (0,1,2):
                    fields=disclosure.build_signwell_fields(code,{'seller_names':['QA']*sellers,'buyer_names':['QA']*buyers})[0]
                    self.assertEqual(len({f['api_id'] for f in fields}),len(fields))
                    self.assertEqual({f['recipient_id'] for f in fields},{str(i+1) for i in range(sellers+buyers)})
                    self.assertTrue(all(f['required'] for f in fields))
