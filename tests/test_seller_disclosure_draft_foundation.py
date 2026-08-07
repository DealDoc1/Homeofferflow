import importlib.util
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "lib" / "seller_disclosure_draft.py"
SPEC = importlib.util.spec_from_file_location("seller_disclosure_draft", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def valid_payload():
    return {
        "formCode": "TREC-55-1",
        "disclosureSourceId": "11111111-1111-4111-8111-111111111111",
        "waterSourceId": "22222222-2222-4222-8222-222222222222",
        "propertyAddress": "1438 Whitaker Road, Van Alstyne, TX 75495",
        "sellerNames": ["Seller One", "Seller Two"],
        "buyerNames": ["Buyer One"],
        "responseData": {"item_1_range_oven": "Y", "question_2_smoke_detectors": "U"},
        "waterRightsData": {"groundwater_district": "unknown"},
    }


class SellerDisclosureDraftTests(unittest.TestCase):
    def test_normalizes_agent_owned_draft_without_attesting_for_seller(self):
        draft = MODULE.parse_seller_disclosure_draft(valid_payload())
        self.assertEqual(draft["status"], "draft")
        self.assertEqual(draft["seller_names"], ["Seller One", "Seller Two"])
        self.assertFalse(draft["seller_review_attested"])
        self.assertEqual(draft["water_rights_data"]["groundwater_district"], "unknown")

    def test_rejects_non_trec_source_or_review_attestation(self):
        with self.assertRaisesRegex(ValueError, "TREC-55-1"):
            MODULE.parse_seller_disclosure_draft({**valid_payload(), "formCode": "TXR-1406"})
        with self.assertRaisesRegex(ValueError, "seller"):
            MODULE.parse_seller_disclosure_draft({**valid_payload(), "sellerReviewAttested": True})

    def test_rejects_missing_sellers_and_excess_names(self):
        with self.assertRaises(ValueError):
            MODULE.parse_seller_disclosure_draft({**valid_payload(), "sellerNames": []})
        with self.assertRaises(ValueError):
            MODULE.parse_seller_disclosure_draft({**valid_payload(), "sellerNames": ["A", "B", "C"]})

    def test_rejects_oversized_response_payload(self):
        with self.assertRaisesRegex(ValueError, "too large"):
            MODULE.parse_seller_disclosure_draft({
                **valid_payload(),
                "responseData": {"notes": "x" * 260000},
            })


class SellerDisclosureFoundationContractTests(unittest.TestCase):
    def test_migration_and_api_remain_draft_only(self):
        migration = (ROOT / "supabase" / "homeofferflow_seller_disclosure_drafts.sql").read_text()
        api = (ROOT / "api" / "admin-dashboard.py").read_text()
        self.assertIn("hof_seller_disclosure_drafts", migration)
        self.assertIn("seller_review_attested", migration)
        self.assertIn("status = 'draft'", migration)
        self.assertIn("create_seller_disclosure_draft", api)
        self.assertIn("workflowActivated", api)
        self.assertIn("preview_seller_disclosure", api)
        self.assertIn("_render_seller_disclosure_draft_preview", api)
        self.assertIn("render_unsigned_preview", api)
        self.assertIn("draft_id", api)
        self.assertNotIn("signwell_document_id", migration)

if __name__ == "__main__":
    unittest.main()
