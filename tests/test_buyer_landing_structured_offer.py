from pathlib import Path
import json
import re
import unittest


BUYERS = (Path(__file__).resolve().parents[1] / "buyers.html").read_text(encoding="utf-8")


class BuyerLandingStructuredOfferTests(unittest.TestCase):
    def test_buyer_landing_exposes_software_application_offer(self):
        blocks = re.findall(r'<script type="application/ld\+json">\s*(.*?)\s*</script>', BUYERS, re.S)
        documents = [json.loads(block) for block in blocks]
        app = next(document for document in documents if document.get("@type") == "SoftwareApplication")
        self.assertEqual(app["url"], "https://www.homeofferflow.com/buyers")
        self.assertEqual(app["offers"]["price"], "99")
        self.assertEqual(app["offers"]["priceCurrency"], "USD")
        self.assertEqual(app["operatingSystem"], "Web")


if __name__ == "__main__":
    unittest.main()
