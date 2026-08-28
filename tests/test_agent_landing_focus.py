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
        self.assertIn('No brokerage seat required.', script)
        self.assertIn("released shared form workflows", script)


if __name__ == '__main__':
    unittest.main()
