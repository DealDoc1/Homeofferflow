"""Independent printed-rule bounds for the owner's purchase-packet defects."""
from io import BytesIO
from pathlib import Path
import unittest

import pdfplumber
from pypdf import PdfReader

from lib import production_adapter as adapter
from lib.trec_20_19_contacts import answer_layout
from tests.test_controlled_launch import configure_local_forms, minimal_offer


ROOT = Path(__file__).resolve().parents[1]


def contact_offer(**overrides):
    values = dict(
        hasBuyerAgent="yes", agentBrokerage="QA Realty", agentName="QAAssociate",
        agentBrokerLicense="9012345", teamName="QATeam", agentLicense="0712345",
        agentEmail="agent@example.com", agentPhone="9725550100",
        buyerMailAddr="123 QA Lane, Frisco, TX 75034", buyerPhone="2145550100",
    )
    values.update(overrides)
    return minimal_offer(**values)


class PurchaseContractSourceAlignmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        configure_local_forms()

    def test_broker_values_clear_printed_labels_and_end_above_their_own_rules(self):
        # Source rule edges, independently measured on page 11. Previous test
        # ranges accepted a value in the space below its named blank.
        expected = {
            "QA": (51, 284.88, 284, 296.28),
            "9012345": (177, 555, 313, 325.08),
            "QAAssociate": (147.48, 555, 327, 339.60),
            "QATeam": (123, 555, 341.5, 354.00),
            "agent@example.com": (146.04, 555, 356, 368.40),
            "9725550100": (167.52, 312, 370, 382.92),
            "0712345": (420.72, 555, 370, 382.92),
        }
        packet = adapter.fill_and_merge_20_19(contact_offer())
        with pdfplumber.open(BytesIO(packet)) as doc, pdfplumber.open(ROOT / "20-19_0.pdf") as source:
            words = doc.pages[10].extract_words()
            rules = source.pages[10].horizontal_edges
            for token, (left, right, top, bottom) in expected.items():
                with self.subTest(value=token):
                    self.assertTrue(any(abs(e["x0"] - left) < .02 and abs(e["top"] - bottom) < .02
                                        for e in rules), "Expected independent source rule")
                    word = next(w for w in words if w["text"] == token)
                    self.assertGreaterEqual(word["x0"], left)
                    self.assertLessEqual(word["x1"], right)
                    self.assertGreaterEqual(word["top"], top)
                    self.assertLessEqual(word["bottom"], bottom)

    def test_address_fields_never_substitute_the_brokerage_name(self):
        packet = adapter.fill_and_merge_20_19(contact_offer())
        reader = PdfReader(BytesIO(packet))
        self.assertNotIn("QA Realty", reader.pages[7].extract_text())
        self.assertIn("QA Realty", reader.pages[10].extract_text())
        self.assertEqual(len(reader.pages), 12)

    def test_supplied_agent_address_and_legacy_mail_address_use_both_correct_blanks(self):
        for key in ("agentAddress", "agentMailAddr"):
            with self.subTest(key=key):
                packet = adapter.fill_and_merge_20_19(contact_offer(**{key: "321 QA Avenue"}))
                reader = PdfReader(BytesIO(packet))
                for page in (7, 10):
                    self.assertIn("321 QA Avenue", reader.pages[page].extract_text())
                with pdfplumber.open(BytesIO(packet)) as doc:
                    words = doc.pages[10].extract_words()
                    word = next(w for w in words if w["text"] == "321")
                    self.assertGreaterEqual(word["x0"], 104.52)
                    self.assertLessEqual(word["bottom"], 310.68)

    def test_full_signature_and_date_rectangles_end_above_the_actual_execution_rules(self):
        for count in (1, 2):
            offer = contact_offer(**({"buyer2": "QA Buyer Two", "buyer2Email": "second@example.com"}
                                     if count == 2 else {}))
            packet = adapter.fill_and_merge_20_19(offer)
            fields = adapter.build_signwell_fields_20_19(offer, packet)[0]
            with pdfplumber.open(ROOT / "20-19_0.pdf") as source:
                rules = [e for e in source.pages[9].horizontal_edges
                         if abs(e["x0"] - 72.01) < .02 and 300 < e["top"] < 500]
            for number, rule_y in ((1, 336.27), (2, 444.97)):
                self.assertTrue(any(abs(e["top"] - rule_y) < .02 for e in rules))
                for kind in ("signature", "date"):
                    matches = [f for f in fields if f["api_id"] == f"buyer{number}_main_contract_{kind}"]
                    self.assertEqual(len(matches), int(number <= count))
                    for field in matches:
                        self.assertEqual(field["page"], 10)
                        self.assertEqual(field["recipient_id"], str(number))
                        self.assertGreaterEqual(field["x"] * .75, 72.01)
                        self.assertLessEqual((field["x"] + field["width"]) * .75, 297.03)
                        self.assertLessEqual((field["y"] + field["height"]) * .75, rule_y - 2)
        self.assertGreater((433 + 20) * .75, 336.27, "Old first signature map must fail this bound")

    def test_main_initial_rectangles_do_not_cross_the_footer_rule(self):
        offer = contact_offer(buyer2="QA Buyer Two", buyer2Email="second@example.com")
        packet = adapter.fill_and_merge_20_19(offer)
        fields = adapter.build_signwell_fields_20_19(offer, packet)[0]
        with pdfplumber.open(ROOT / "20-19_0.pdf") as source:
            for field in fields:
                if "initials_main" not in field["api_id"]:
                    continue
                edges = [e for e in source.pages[field["page"] - 1].horizontal_edges
                         if 200 <= e["x0"] < 290 and 760 < e["top"] < 775 and 30 < e["width"] < 40]
                self.assertTrue(edges)
                self.assertLessEqual((field["y"] + field["height"]) * .75,
                                     min(e["top"] for e in edges) - 2)

    def test_very_long_unicode_contacts_are_preserved_in_an_initialed_continuation(self):
        name = "Élodie Hernández " * 65
        email = "long" * 70 + "@example.com"
        offer = contact_offer(agentName=name, agentEmail=email,
                              buyer2="QA Buyer Two", buyer2Email="second@example.com")
        packet = adapter.fill_and_merge_20_19(offer)
        reader = PdfReader(BytesIO(packet))
        self.assertGreater(len(reader.pages), 12)
        text = " ".join((p.extract_text() or "") for p in reader.pages[12:])
        self.assertIn("Buyer associate name", text)
        self.assertEqual(text.count("Élodie"), 65)
        self.assertIn(email, text.replace("\n", ""))
        fields = adapter.build_signwell_fields_20_19(offer, packet)[0]
        contacts = [f for f in fields if f["api_id"].startswith("contacts_continuation_")]
        self.assertEqual(len(contacts), (len(reader.pages) - 12) * 2)
        self.assertEqual({f["recipient_id"] for f in contacts}, {"1", "2"})
        self.assertEqual({f["page"] for f in contacts}, set(range(13, len(reader.pages) + 1)))
        answers = answer_layout(offer)
        self.assertIn("Buyer associate name", answers.overflow)
        self.assertEqual(answers.overflow["Buyer associate name"], " ".join(name.split()))


if __name__ == "__main__":
    unittest.main()
