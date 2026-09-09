"""Structural placement guards for private TXR SignWell field maps.

These checks do not replace rendered-PDF or completed-signature review. They
catch the inexpensive failures that otherwise make that review unreliable:
missing signer fields, duplicate field IDs, invalid page numbers, zero-sized
widgets, overlapping widgets for one signer, and date fields detached from
their corresponding signature/initials field.
"""

import unittest

from lib.txr_1501 import build_signwell_fields_txr1501
from lib.txr_1506 import build_signwell_fields_txr1506
from lib.txr_1507 import build_signwell_fields_txr1507
from lib.txr_1508 import build_signwell_fields_txr1508
from lib.txr_1953 import build_signwell_fields_txr1953
from lib.txr_1954 import build_signwell_fields_txr1954


FORM_CASES = (
    ("TXR-1501", 6, build_signwell_fields_txr1501, {
        "client_names": ["Client One", "Client Two"],
        "market_area": "Texas",
        "term_start": "2026-08-01",
        "term_end": "2027-01-31",
        "client_address": "1 Main Street",
        "client_city_state_zip": "Prosper, TX 75078",
        "client_phone": "2143649890",
        "client_email": "client@example.com",
        "compensation": {"purchase_percentage": "3"},
        "retainer_amount": "",
        "retainer_treatment": "",
        "protection_days": "30",
        "payment_county": "Collin",
        "intermediary": "authorized",
        "signer_plan": "clients_and_associate",
    }),
    ("TXR-1506", 6, build_signwell_fields_txr1506, {
        "client_names": ["Consumer One", "Consumer Two"],
        "additional_notice": "Review the notice before acknowledging it.",
        "signer_plan": "consumers_and_associate",
    }),
    ("TXR-1507", 2, build_signwell_fields_txr1507, {
        "client_names": ["Client One", "Client Two"],
        "market_area": "Texas",
        "term_start": "2026-08-01",
        "term_end": "2027-01-31",
        "service_level": "full_services",
        "showing_fee": "",
        "compensation": {"purchase_percentage": "3"},
        "intermediary": "authorized",
        "signer_plan": "clients_and_associate",
    }),
    ("TXR-1508", 1, build_signwell_fields_txr1508, {
        "property_address": "1 Main Street, Texas",
        "client_names": ["Customer One", "Customer Two"],
        "other_broker_agreement": ["no", "yes"],
        "signer_plan": "associate_and_clients",
    }),
    ("TXR-1953", 1, build_signwell_fields_txr1953, {
        "buyer_names": ["Buyer One", "Buyer Two"],
        "seller_names": ["Seller One", "Seller Two"],
    }),
    ("TXR-1954", 1, build_signwell_fields_txr1954, {
        "buyer_names": ["Buyer One", "Buyer Two"],
        "seller_names": ["Seller One", "Seller Two"],
    }),
)

# SignWell's field API uses a 96-DPI, top-origin US Letter page.  A field
# outside this canvas may be accepted by the API yet be impossible to see or
# complete in the signing ceremony.
SIGNWELL_LETTER_WIDTH = 816
SIGNWELL_LETTER_HEIGHT = 1056


def _rectangles_overlap(left, right):
    if left["page"] != right["page"] or left["recipient_id"] != right["recipient_id"]:
        return False
    return not (
        left["x"] + left["width"] <= right["x"]
        or right["x"] + right["width"] <= left["x"]
        or left["y"] + left["height"] <= right["y"]
        or right["y"] + right["height"] <= left["y"]
    )


class TxrSignerGeometryTests(unittest.TestCase):
    def test_completed_packet_signature_maps_keep_dates_off_the_printed_date_labels(self):
        """Guard the source-calibrated 1501/1507 signature rows.

        These maps were calibrated against completed SignWell packets.  The
        date widget must end before the preprinted Date label, while the
        signature widget remains on the same ruled row.
        """
        cases = (
            (build_signwell_fields_txr1501, FORM_CASES[0][3], "txr1501", 568, 700),
            (build_signwell_fields_txr1507, FORM_CASES[2][3], "txr1507", 695, 700),
        )
        for builder, data, prefix, first_row_y, date_label_x in cases:
            with self.subTest(prefix=prefix):
                fields = {field["api_id"]: field for field in builder(data, client_count=2)[0]}
                client = fields[f"{prefix}_client1_signature_p{6 if prefix == 'txr1501' else 2}"]
                date = fields[f"{prefix}_client1_date_p{6 if prefix == 'txr1501' else 2}"]
                role = fields[f"{prefix}_associate_signature_p{6 if prefix == 'txr1501' else 2}"]
                self.assertEqual(client["y"], first_row_y)
                self.assertEqual(role["y"], first_row_y)
                self.assertGreater(date["x"], client["x"] + client["width"])
                self.assertLessEqual(date["x"] + date["width"], date_label_x)

    def test_txr1506_provider_and_consumer_dates_share_the_printed_date_column(self):
        """Keep every page-six acknowledgement date on TXR-1506's right rule.

        The broker/associate acknowledgement has the same Date column as the
        two consumer acknowledgements.  A left-shifted provider date can look
        superficially valid to SignWell while covering the signature caption.
        """
        data = FORM_CASES[1][3]
        fields = {
            field["api_id"]: field
            for field in build_signwell_fields_txr1506(data, client_count=2)[0]
        }
        for field_id, row_y in (
            ("txr1506_associate_date_p6", 800),
            ("txr1506_client1_date_p6", 893),
            ("txr1506_client2_date_p6", 939),
        ):
            with self.subTest(field_id=field_id):
                self.assertEqual(fields[field_id]["x"], 455)
                self.assertEqual(fields[field_id]["y"], row_y)

    def test_paragraph4_signatures_stay_on_the_source_rules_above_party_labels(self):
        """Keep the buyer/seller widgets on the calibrated TXR-1953/1954 rules.

        Both one-page Paragraph 4 addenda print the party label immediately
        below each signature rule.  A harmless-looking downward move can
        therefore cover ``Buyer`` or ``Seller`` in a completed packet.  These
        bounds are based on the released source PDFs, not a blank fixture.
        """
        cases = (
            ("TXR-1953", build_signwell_fields_txr1953, FORM_CASES[4][3], 70, 440, 802, 875, 828, 901),
            ("TXR-1954", build_signwell_fields_txr1954, FORM_CASES[5][3], 64, 418, 774, 845, 800, 871),
        )
        for form_code, builder, data, buyer_x, seller_x, first_y, second_y, first_bottom, second_bottom in cases:
            with self.subTest(form_code=form_code):
                fields = {field["api_id"]: field for field in builder(data, client_count=2)[0]}
                for party, x in (("buyer", buyer_x), ("seller", seller_x)):
                    first = fields[f"{form_code.lower().replace('-', '')}_{party}1_signature_p1"]
                    second = fields[f"{form_code.lower().replace('-', '')}_{party}2_signature_p1"]
                    self.assertEqual(first["x"], x)
                    self.assertEqual(second["x"], x)
                    self.assertEqual(first["y"], first_y)
                    self.assertEqual(second["y"], second_y)
                    self.assertLessEqual(first["y"] + first["height"], first_bottom)
                    self.assertLessEqual(second["y"] + second["height"], second_bottom)

    def test_every_supported_form_has_valid_non_overlapping_signer_widgets(self):
        for form_code, page_count, builder, data in FORM_CASES:
            with self.subTest(form_code=form_code):
                fields = builder(data, client_count=2)[0]
                self.assertTrue(fields, "a supported form must expose signer widgets")
                self.assertEqual(len({field["api_id"] for field in fields}), len(fields))
                for field in fields:
                    self.assertIn(field["page"], range(1, page_count + 1))
                    self.assertIn(field["type"], {"signature", "initials", "date"})
                    self.assertTrue(field["required"])
                    self.assertGreater(field["width"], 0)
                    self.assertGreater(field["height"], 0)
                    self.assertGreaterEqual(field["x"], 0)
                    self.assertGreaterEqual(field["y"], 0)
                    self.assertLessEqual(
                        field["x"] + field["width"], SIGNWELL_LETTER_WIDTH,
                        f"{form_code} field falls beyond the right page edge: {field['api_id']}",
                    )
                    self.assertLessEqual(
                        field["y"] + field["height"], SIGNWELL_LETTER_HEIGHT,
                        f"{form_code} field falls beyond the bottom page edge: {field['api_id']}",
                    )
                for index, field in enumerate(fields):
                    for other in fields[index + 1:]:
                        self.assertFalse(
                            _rectangles_overlap(field, other),
                            f"{form_code} has overlapping widgets: {field['api_id']} / {other['api_id']}",
                        )

    def test_date_widgets_are_on_the_same_page_and_signer_as_their_counterpart(self):
        for form_code, _, builder, data in FORM_CASES:
            with self.subTest(form_code=form_code):
                fields = builder(data, client_count=2)[0]
                by_id = {field["api_id"]: field for field in fields}
                for field in fields:
                    if field["type"] != "date":
                        continue
                    counterpart_id = field["api_id"].replace("_date_", "_signature_")
                    if counterpart_id not in by_id:
                        counterpart_id = field["api_id"].replace("_date_", "_initials_")
                    self.assertIn(counterpart_id, by_id, f"{form_code} date lacks a counterpart")
                    counterpart = by_id[counterpart_id]
                    self.assertEqual(field["page"], counterpart["page"])
                    self.assertEqual(field["recipient_id"], counterpart["recipient_id"])
                    self.assertGreater(field["x"], counterpart["x"])
                    self.assertLessEqual(
                        abs((field["y"] + field["height"] / 2) - (counterpart["y"] + counterpart["height"] / 2)),
                        8,
                        f"{form_code} date is not aligned with its signer row: {field['api_id']}",
                    )


if __name__ == "__main__":
    unittest.main()
