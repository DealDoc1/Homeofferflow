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
from lib.txr_1905 import build_signwell_fields_txr1905
from lib.txr_1914 import build_signwell_fields_txr1914
from lib.txr_1917 import build_signwell_fields_txr1917
from lib.txr_1919 import build_signwell_fields_txr1919
from lib.txr_1948 import build_signwell_fields_txr1948
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
    ("TXR-1905", 1, build_signwell_fields_txr1905, {
        "buyer_names": ["Buyer One", "Buyer Two"],
        "seller_names": ["Seller One", "Seller Two"],
    }),
    ("TXR-1914", 2, build_signwell_fields_txr1914, {
        "buyer_names": ["Buyer One", "Buyer Two"],
        "seller_names": ["Seller One", "Seller Two"],
    }),
    ("TXR-1917", 1, build_signwell_fields_txr1917, {
        "buyer_names": ["Buyer One", "Buyer Two"],
        "seller_names": ["Seller One", "Seller Two"],
    }),
    ("TXR-1919", 2, build_signwell_fields_txr1919, {
        "buyer_names": ["Buyer One", "Buyer Two"],
        "seller_names": ["Seller One", "Seller Two"],
    }),
    ("TXR-1948", 1, build_signwell_fields_txr1948, {
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
        date widget must leave room for SignWell's visible date stamp before
        the preprinted Date label, while the signature widget remains on the
        same ruled row.
        """
        cases = (
            (build_signwell_fields_txr1501, FORM_CASES[0][3], "txr1501", 566, 535),
            # The completed packet shows the printed client Date caption
            # farther right than the earlier nominal bound. Keep the date in
            # that dedicated execution space, rather than beside the
            # signature field.
            (build_signwell_fields_txr1507, FORM_CASES[2][3], "txr1507", 640, 630),
        )
        for builder, data, prefix, first_row_y, date_label_x in cases:
            with self.subTest(prefix=prefix):
                fields = {field["api_id"]: field for field in builder(data, client_count=2)[0]}
                client = fields[f"{prefix}_client1_signature_p{6 if prefix == 'txr1501' else 2}"]
                date = fields[f"{prefix}_client1_date_p{6 if prefix == 'txr1501' else 2}"]
                role = fields[f"{prefix}_associate_signature_p{6 if prefix == 'txr1501' else 2}"]
                self.assertEqual(client["y"], first_row_y)
                if prefix == "txr1507":
                    self.assertEqual(role["y"], 590)
                else:
                    self.assertEqual(role["y"], 677)
                self.assertGreater(date["x"], client["x"] + client["width"])
                # The provider's completed-packet renderer may let a full
                # MM/DD/YYYY value extend beyond the nominal widget width.
                # Reserve that observed 20-pixel right-side footprint rather
                # than passing a map that only looks safe while empty.
                self.assertLessEqual(date["x"] + date["width"] + 20, date_label_x)

    def test_corrected_signature_rows_clear_the_caption_baseline(self):
        """Keep active maps above the printed signature/date captions.

        The earlier active maps used printed-name or caption coordinates.
        These bounds keep a future coordinate change from dropping a signer
        back onto the labels printed beneath each execution rule.
        """
        cases = (
            (build_signwell_fields_txr1501, FORM_CASES[0][3], {
                "txr1501_associate_signature_p6": 701,
                "txr1501_associate_date_p6": 701,
                "txr1501_client1_signature_p6": 590,
                "txr1501_client1_date_p6": 590,
                "txr1501_client2_signature_p6": 701,
                "txr1501_client2_date_p6": 701,
            }),
            (build_signwell_fields_txr1507, FORM_CASES[2][3], {
                "txr1507_associate_signature_p2": 692,
                "txr1507_associate_date_p2": 692,
                "txr1507_client1_signature_p2": 692,
                "txr1507_client1_date_p2": 692,
                "txr1507_client2_signature_p2": 791,
                "txr1507_client2_date_p2": 791,
            }),
        )
        for builder, data, limits in cases:
            with self.subTest(builder=builder.__name__):
                fields = {field["api_id"]: field for field in builder(data, client_count=2)[0]}
                self.assertEqual(set(fields) & set(limits), set(limits))
                for api_id, caption_y in limits.items():
                    self.assertLessEqual(fields[api_id]["y"] + fields[api_id]["height"], caption_y)

    def test_txr1501_second_client_and_txr1507_associate_use_their_actual_rules(self):
        """Keep both source rows clear of captions beneath the signing rules."""
        txr1501 = {
            field["api_id"]: field
            for field in build_signwell_fields_txr1501(FORM_CASES[0][3], client_count=2)[0]
        }
        # On the released source the second-client rule is above the printed
        # caption. A 24-unit signature field must finish before the caption,
        # not over the
        # printed Client's Signature caption below it.
        self.assertEqual(txr1501["txr1501_client2_signature_p6"]["y"], 677)
        self.assertEqual(
            txr1501["txr1501_client2_signature_p6"]["y"]
            + txr1501["txr1501_client2_signature_p6"]["height"],
            701,
        )
        # A broker-associate signs the separate lower left row.  It shares
        # that horizontal line with the second client's right-side row, not
        # the broker's first execution row.
        self.assertEqual(txr1501["txr1501_associate_signature_p6"]["y"], 677)
        self.assertEqual(
            txr1501["txr1501_associate_signature_p6"]["y"]
            + txr1501["txr1501_associate_signature_p6"]["height"],
            701,
        )

        txr1507 = {
            field["api_id"]: field
            for field in build_signwell_fields_txr1507(FORM_CASES[2][3], client_count=2)[0]
        }
        # Broker and broker-associate are chosen by the printed checkboxes;
        # both sign on the one shared rule.  There is no second associate
        # signature rule below the label.
        self.assertEqual(txr1507["txr1507_associate_signature_p2"]["y"], 590)
        self.assertEqual(txr1507["txr1507_associate_signature_p2"]["x"], 10)
        self.assertEqual(txr1507["txr1507_associate_date_p2"]["x"], 185)
        self.assertEqual(
            (txr1507["txr1507_associate_initials_p1"]["x"], txr1507["txr1507_associate_initials_p1"]["y"]),
            (435, 984),
        )
        self.assertEqual(txr1507["txr1507_client1_initials_p1"]["x"], 542)
        self.assertEqual(txr1507["txr1507_client2_initials_p1"]["x"], 596)

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
                self.assertEqual(fields[field_id]["x"], 432)
                self.assertEqual(fields[field_id]["width"], 96)
                self.assertEqual(fields[field_id]["y"], row_y)
        # Unlike the consumer rows, the provider row is prefixed by the
        # source's printed "By:". Its signer widget must begin after that
        # prefix instead of obscuring it in the SignWell ceremony.
        self.assertEqual(fields["txr1506_associate_signature_p6"]["x"], 80)
        self.assertEqual(fields["txr1506_associate_signature_p6"]["width"], 304)
        self.assertEqual(fields["txr1506_associate_signature_p6"]["y"] + fields["txr1506_associate_signature_p6"]["height"], 825)
        for field_id in ("txr1506_client1_signature_p6", "txr1506_client2_signature_p6"):
            with self.subTest(field_id=field_id):
                self.assertEqual((fields[field_id]["x"], fields[field_id]["width"]), (48, 336))

    def test_paragraph4_signatures_stay_on_the_source_rules_above_party_labels(self):
        """Keep the buyer/seller widgets on the calibrated TXR-1953/1954 rules.

        Both one-page Paragraph 4 addenda print the party label immediately
        below each signature rule.  A harmless-looking downward move can
        therefore cover ``Buyer`` or ``Seller`` in a completed packet.  These
        bounds are based on the released source PDFs, not a blank fixture.
        """
        cases = (
            ("TXR-1953", build_signwell_fields_txr1953, FORM_CASES[4][3], 70, 440, 306, 302, 802, 875, 828, 901),
            ("TXR-1954", build_signwell_fields_txr1954, FORM_CASES[5][3], 64, 418, 335, 324, 774, 876, 800, 902),
        )
        for form_code, builder, data, buyer_x, seller_x, buyer_width, seller_width, first_y, second_y, first_bottom, second_bottom in cases:
            with self.subTest(form_code=form_code):
                fields = {field["api_id"]: field for field in builder(data, client_count=2)[0]}
                for party, x in (("buyer", buyer_x), ("seller", seller_x)):
                    first = fields[f"{form_code.lower().replace('-', '')}_{party}1_signature_p1"]
                    second = fields[f"{form_code.lower().replace('-', '')}_{party}2_signature_p1"]
                    self.assertEqual(first["x"], x)
                    self.assertEqual(second["x"], x)
                    self.assertEqual(first["width"], buyer_width if party == "buyer" else seller_width)
                    self.assertEqual(second["width"], buyer_width if party == "buyer" else seller_width)
                    self.assertEqual(first["y"], first_y)
                    self.assertEqual(second["y"], second_y)
                    # The source rows are rules immediately above the printed
                    # Buyer/Seller captions.  Ending short makes a signature
                    # look detached; extending below the rule covers the
                    # caption in the completed SignWell PDF.  These values
                    # were rechecked visually against the approved sources.
                    self.assertEqual(first["y"] + first["height"], first_bottom)
                    self.assertEqual(second["y"] + second["height"], second_bottom)

    def test_addendum_signatures_end_at_their_source_rules(self):
        """Keep the newer addendum signatures above their printed party labels.

        All values are in the 96-DPI, top-origin SignWell coordinate space.
        The source-rule bottoms were measured from the actual TXR PDFs, then
        rounded only where the rendered rule falls between pixels.
        """
        cases = (
            ("txr1905", build_signwell_fields_txr1905, FORM_CASES[6][3], 831, 907),
            ("txr1914", build_signwell_fields_txr1914, FORM_CASES[7][3], 742, 844),
            ("txr1917", build_signwell_fields_txr1917, FORM_CASES[8][3], 710, 804),
            ("txr1919", build_signwell_fields_txr1919, FORM_CASES[9][3], 656, 740),
        )
        for prefix, builder, data, first_bottom, second_bottom in cases:
            with self.subTest(prefix=prefix):
                fields = {field["api_id"]: field for field in builder(data, client_count=2)[0]}
                for party in ("buyer", "seller"):
                    first = fields[f"{prefix}_{party}1_signature_p{1 if prefix in {'txr1905', 'txr1917'} else 2}"]
                    second = fields[f"{prefix}_{party}2_signature_p{1 if prefix in {'txr1905', 'txr1917'} else 2}"]
                    self.assertEqual(first["y"] + first["height"], first_bottom)
                    self.assertEqual(second["y"] + second["height"], second_bottom)

    def test_txr1948_signatures_clear_both_party_captions(self):
        """Keep the appraisal-addendum signer boxes above their two rules.

        TXR-1948 prints Buyer/Seller captions immediately below each
        execution rule.  The fields deliberately stop short of the rules so
        a completed signature cannot cover either the line or its caption.
        """
        fields = {
            field["api_id"]: field
            for field in build_signwell_fields_txr1948(FORM_CASES[10][3], client_count=2)[0]
        }
        for party, x, width in (("buyer", 58, 336), ("seller", 424, 318)):
            first = fields[f"txr1948_{party}1_signature_p1"]
            second = fields[f"txr1948_{party}2_signature_p1"]
            self.assertEqual((first["x"], first["y"], first["y"] + first["height"]), (x, 764, 790))
            self.assertEqual((second["x"], second["y"], second["y"] + second["height"]), (x, 852, 878))
            self.assertEqual(first["width"], width)
            self.assertEqual(second["width"], width)

    def test_txr1508_acknowledgements_clear_their_printed_captions(self):
        """Keep TXR-1508 completion widgets on their acknowledgement rules.

        The agent acknowledgement rule is left of the Date label, while the
        customer acknowledgement rules are on the right below it.  They are
        different source locations even though the fields share a row shape.
        """
        data = FORM_CASES[3][3]
        fields = {
            field["api_id"]: field
            for field in build_signwell_fields_txr1508(data, client_count=2)[0]
        }
        self.assertEqual(fields["txr1508_agent_initials_p1"]["x"], 347)
        self.assertEqual(fields["txr1508_agent_initials_p1"]["y"], 659)
        self.assertLess(
            fields["txr1508_agent_initials_p1"]["x"] + fields["txr1508_agent_initials_p1"]["width"],
            445,
            "agent initials must finish before the printed Date label",
        )
        self.assertEqual(
            (fields["txr1508_client1_initials_p1"]["x"], fields["txr1508_client1_initials_p1"]["width"]),
            (518, 61),
        )
        for field_id in ("txr1508_agent_date_p1", "txr1508_client1_date_p1", "txr1508_client2_date_p1"):
            with self.subTest(field_id=field_id):
                self.assertEqual((fields[field_id]["x"], fields[field_id]["width"]), (625, 121))
        # Captions start at y=678, 734, and 792 in SignWell's 96-DPI
        # coordinate space.  Fields must finish before those captions rather
        # than merely passing the generic bounds/overlap checks.
        expected_caption_tops = {
            "txr1508_agent_initials_p1": 678,
            "txr1508_agent_date_p1": 678,
            "txr1508_client1_initials_p1": 734,
            "txr1508_client1_date_p1": 734,
            "txr1508_client2_initials_p1": 792,
            "txr1508_client2_date_p1": 792,
        }
        for field_id, caption_top in expected_caption_tops.items():
            with self.subTest(field_id=field_id):
                field = fields[field_id]
                self.assertLessEqual(field["y"] + field["height"], caption_top)

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
