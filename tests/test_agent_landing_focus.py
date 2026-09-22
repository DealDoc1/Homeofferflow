import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class AgentLandingFocusTests(unittest.TestCase):
    def test_progressive_focus_asset_is_loaded_and_preserves_resource_paths(self):
        page = (ROOT / 'agents.html').read_text(encoding='utf-8')
        script = (ROOT / 'assets/agent-landing-focus.js').read_text(encoding='utf-8')
        self.assertIn('/assets/agent-landing-focus.css', page)
        self.assertIn('/assets/agent-landing-focus.js', page)
        for path in ('texas-agent-offer-workflow', 'texas-agent-form-library', 'texas-listing-workflow', 'texas-lease-offer-workflow'):
            self.assertIn(path, script)
        self.assertIn('Explore shared forms and workflow guides', script)
        self.assertIn('agent_resource_links_expanded', script)
        self.assertIn('pwa_shortcut', script)
        self.assertIn('site_recovery', script)
        self.assertIn("'organic'", script)
        self.assertIn('No brokerage seat or payment required to start.', script)
        self.assertIn("released shared forms and create a listing workspace", script)
        self.assertIn("Paid plan terms appear before recurring checkout.", script)
        self.assertNotIn("strong.textContent = 'No brokerage seat required.'", script)
        self.assertIn("Offer workflow guide", script)
        self.assertIn("Shared form library", script)


if __name__ == '__main__':
    unittest.main()
