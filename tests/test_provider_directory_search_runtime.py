from pathlib import Path
import json
import re
import shutil
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ProviderDirectorySearchRuntimeTests(unittest.TestCase):
    def test_directory_copy_prioritizes_the_service_and_contact_decision(self):
        source = (ROOT / "directory.html").read_text()
        self.assertIn("<h1>Find local help for your home.</h1>", source)
        self.assertIn("What service do you need?", source)
        self.assertIn('<details class="directory-about">', source)
        self.assertNotIn('<div class="notice">', source)
        self.assertIn('class="placement-label"', source)
        self.assertIn('class="provider-description"', source)

    def test_responsive_layout_uses_available_space_and_supports_no_logo(self):
        source = (ROOT / "directory.html").read_text()
        self.assertIn("repeat(auto-fit,minmax(min(100%,300px),1fr))", source)
        self.assertIn(".grid.single-provider .card.no-logo{grid-template-columns:1fr}", source)
        self.assertIn(".grid.single-provider .card{grid-template-columns:1fr}", source)
        self.assertIn("min-height:44px", source)

    def test_search_metadata_answers_match_the_visible_directory_details(self):
        source = (ROOT / "directory.html").read_text()
        schemas = [json.loads(value) for value in re.findall(
            r'<script type="application/ld\+json">(.*?)</script>', source, re.S
        )]
        faq = next(schema for schema in schemas if schema["@type"] == "FAQPage")
        details = source.split('<details class="directory-about">', 1)[1].split('</details>', 1)[0]
        self.assertEqual(len(faq["mainEntity"]), 2)
        for item in faq["mainEntity"]:
            self.assertIn(item["name"], details)
            self.assertIn(item["acceptedAnswer"]["text"], details)

    def test_actual_directory_handles_races_failures_timeout_and_safe_profiles(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node runtime unavailable")
        result = subprocess.run(
            [node, str(ROOT / "tests/provider_directory_search.runtime.cjs")],
            cwd=ROOT, capture_output=True, text=True, timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("12 actual-source provider search cases passed", result.stdout)


if __name__ == "__main__":
    unittest.main()
