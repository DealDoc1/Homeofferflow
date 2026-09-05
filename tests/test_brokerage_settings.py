from pathlib import Path
import unittest


HTML = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class BrokerageSettingsTests(unittest.TestCase):
    def test_every_visible_brokerage_setting_is_collected_for_save(self):
        start = HTML.index("async function saveBrokerageFoundation()")
        end = HTML.index("function renderSellerFoundationPanel()", start)
        save_function = HTML[start:end]

        for input_id in (
            "brandOrgType",
            "brandSlug",
            "brandBrokerageName",
            "brandDbaName",
            "brandLicense",
            "brandLogoUrl",
            "brandColor",
            "brandWebsiteUrl",
            "brandOfficeAddress",
            "brandOfficeCity",
            "brandOfficeState",
            "brandOfficeZip",
            "brandContactName",
            "brandContactEmail",
            "brandContactPhone",
            "brandDisclaimer",
            "brandDefaultTitle",
        ):
            with self.subTest(input_id=input_id):
                self.assertIn(f"getVal('{input_id}')", save_function)

    def test_legacy_schema_fallback_removes_only_optional_new_columns(self):
        self.assertIn("const { org_type, slug, office_address, office_city, office_state, office_zip, ...legacyPayload } = payload;", HTML)


if __name__ == "__main__":
    unittest.main()
