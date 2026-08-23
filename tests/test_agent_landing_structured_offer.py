from pathlib import Path
import json
import unittest


HTML = (Path(__file__).resolve().parents[1] / "agents.html").read_text(encoding="utf-8")
INVESTORS_HTML = (Path(__file__).resolve().parents[1] / "investors.html").read_text(encoding="utf-8")


class AgentLandingStructuredOfferTests(unittest.TestCase):
    def test_agent_software_application_declares_no_charge_entry_offer(self):
        marker = '<script type="application/ld+json">'
        scripts = []
        remainder = HTML
        while marker in remainder:
            _, tail = remainder.split(marker, 1)
            raw, remainder = tail.split("</script>", 1)
            scripts.append(json.loads(raw.strip()))
        app = next(item for item in scripts if item.get("@type") == "SoftwareApplication")
        self.assertEqual(app["offers"]["price"], "0")
        self.assertEqual(app["offers"]["priceCurrency"], "USD")
        self.assertIn("before checkout", app["offers"]["description"])

    def test_investor_software_application_declares_no_charge_entry_offer(self):
        marker = '<script type="application/ld+json">'
        scripts = []
        remainder = INVESTORS_HTML
        while marker in remainder:
            _, tail = remainder.split(marker, 1)
            raw, remainder = tail.split("</script>", 1)
            try:
                scripts.append(json.loads(raw.strip()))
            except json.JSONDecodeError:
                continue
        app = next(item for item in scripts if item.get("@type") == "SoftwareApplication")
        self.assertEqual(app["offers"]["price"], "0")
        self.assertEqual(app["offers"]["priceCurrency"], "USD")
        self.assertIn("before checkout", app["offers"]["description"])


if __name__ == "__main__":
    unittest.main()
