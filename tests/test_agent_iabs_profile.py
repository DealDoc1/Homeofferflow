import base64
from io import BytesIO
from pathlib import Path
import unittest

from pypdf import PdfReader, PdfWriter

from lib import production_adapter as adapter


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
MIGRATION = (ROOT / "supabase" / "homeofferflow_agent_iabs_profile.sql").read_text(
    encoding="utf-8"
)


def one_page_pdf_base64():
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    output = BytesIO()
    writer.write(output)
    return base64.b64encode(output.getvalue()).decode()


class AgentIabsProfileTests(unittest.TestCase):
    def test_iabs_profile_is_private_user_owned_pdf_storage(self):
        self.assertIn("create table if not exists public.hof_agent_documents", MIGRATION)
        self.assertIn("document_type in ('iabs')", MIGRATION)
        self.assertIn("'agent-documents'", MIGRATION)
        self.assertIn("public, file_size_limit, allowed_mime_types", MIGRATION)
        self.assertIn("false,", MIGRATION)
        self.assertIn("array['application/pdf']", MIGRATION)
        self.assertIn("(storage.foldername(name))[1] = (select auth.uid()::text)", MIGRATION)
        self.assertIn("for select to authenticated", MIGRATION)
        self.assertIn("for insert to authenticated", MIGRATION)
        self.assertIn("for update to authenticated", MIGRATION)
        self.assertIn("for delete to authenticated", MIGRATION)

    def test_profile_and_offer_controls_are_optional_and_not_auto_attached(self):
        self.assertIn("<h4>My IABS</h4>", HTML)
        self.assertIn("Include my IABS?", HTML)
        self.assertIn("It is never attached automatically.", HTML)
        self.assertIn("['agent', 'broker', 'brokerage_admin', 'team_lead'].includes(role)", HTML)
        self.assertIn("!!root.hofAuth?.session?.user", HTML)
        self.assertIn("includeAgentIabs", HTML)
        self.assertIn("if (!isAgentAccount() || !root.state?.data?.includeAgentIabs) return null;", HTML)
        self.assertIn("needsBuyerSignature: false", HTML)
        self.assertIn("needsBuyerInitials: false", HTML)

    def test_selected_profile_iabs_uses_existing_safe_upload_append_path(self):
        self.assertIn("const profileIabsDoc = await window.getProfileIabsOfferDoc?.();", HTML)
        self.assertIn("...(profileIabsDoc ? [profileIabsDoc] : [])", HTML)

    def test_iabs_pdf_can_append_without_new_signature_fields(self):
        docs = adapter._uploaded_docs({
            "uploadedDisclosureDocs": [{
                "name": "approved-iabs.pdf",
                "type": "agent_iabs_profile",
                "needsBuyerSignature": False,
                "needsBuyerInitials": False,
                "base64": one_page_pdf_base64(),
            }]
        })
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0]["name"], "approved-iabs.pdf")
        self.assertEqual(docs[0]["page_count"], 1)


if __name__ == "__main__":
    unittest.main()
