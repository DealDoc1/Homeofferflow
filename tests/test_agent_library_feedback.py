from pathlib import Path
import unittest


INDEX = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class AgentLibraryFeedbackTests(unittest.TestCase):
    def test_remaining_agent_library_actions_have_no_browser_alerts(self):
        for marker in (
            "copyMissingFormIntakeBrief",
            "root.uploadAgentIabsDocument",
            "async function uploadSource()",
            "renderPlatformSourceIntake",
            "renderPrivateDraftsCard",
            "hofStandaloneAgreementCard",
        ):
            start = INDEX.find(marker)
            self.assertGreaterEqual(start, 0, marker)
            end = INDEX.find("</script>", start)
            self.assertGreater(end, start, marker)
            self.assertNotIn("alert(", INDEX[start:end], marker)

    def test_agent_library_surfaces_expose_status_regions(self):
        for expected in (
            'id="agentIabsStatus"',
            'id="brokerageFormSourceStatus"',
            'id="platformSourceStatus"',
            'id="privateFormDraftsStatus"',
            "window.announceWorkspaceStatus?.(",
        ):
            self.assertIn(expected, INDEX)

    def test_empty_private_drafts_offer_a_return_to_transaction_router(self):
        self.assertIn('No saved form drafts yet.<br><button', INDEX)
        self.assertIn('data-start-agent-transaction', INDEX)
        self.assertIn("document.getElementById('agentWorkflowStart')", INDEX)

    def test_private_pdf_previews_stay_inside_the_workspace(self):
        """Avoid both popup blocking and a cluttered tab bar for draft review."""
        self.assertNotIn("window.open('', '_blank')", INDEX)
        self.assertIn("root.hofShowPdfPreview = function hofShowPdfPreview", INDEX)
        self.assertEqual(INDEX.count("root.hofShowPdfPreview(await response.blob()"), 2)
        self.assertIn("root.hofShowPdfPreview(blob, draft?.form_code);", INDEX)
        self.assertIn("URL.revokeObjectURL(blobUrl)", INDEX)


if __name__ == "__main__":
    unittest.main()
