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
)


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


if __name__ == "__main__":
    unittest.main()
