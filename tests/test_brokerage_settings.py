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

    def test_logo_upload_is_limited_to_safe_brand_image_types(self):
        start = HTML.index("async function uploadBrokerageLogo()")
        end = HTML.index("function renderSellerFoundationPanel()", start)
        upload_function = HTML[start:end]
        for image_type in ("image/png", "image/jpeg", "image/webp", "image/svg+xml"):
            self.assertIn(image_type, upload_function)
        self.assertIn("2 * 1024 * 1024", upload_function)
        self.assertIn("client.storage.from('brokerage-branding').upload", upload_function)

    def test_logo_storage_policy_is_limited_to_the_admins_brokerage(self):
        root = Path(__file__).resolve().parents[1]
        sql = (root / "supabase" / "homeofferflow_brokerage_branding_storage.sql").read_text(encoding="utf-8")
        self.assertIn("bucket_id = 'brokerage-branding'", sql)
        self.assertIn("profile.brokerage_id::text = (storage.foldername(name))[1]", sql)
        self.assertIn("to authenticated", sql)


if __name__ == "__main__":
    unittest.main()
