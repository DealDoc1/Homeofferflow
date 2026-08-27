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
        self.assertIn('No private form drafts saved yet.<br><button', INDEX)
        self.assertIn('data-start-agent-transaction', INDEX)
        self.assertIn("document.getElementById('agentWorkflowStart')", INDEX)

    def test_private_pdf_previews_open_synchronously_before_fetching(self):
        """Avoid browser popup blocking after the async authenticated preview fetch."""
        self.assertEqual(INDEX.count("const previewWindow = window.open('', '_blank');"), 3)
        self.assertEqual(INDEX.count('previewWindow.location.replace(url);'), 3)
        self.assertEqual(INDEX.count('previewWindow?.close();'), 3)


if __name__ == "__main__":
    unittest.main()
