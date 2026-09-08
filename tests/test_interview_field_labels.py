from pathlib import Path
import unittest


HTML = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class InterviewFieldLabelTests(unittest.TestCase):
    def test_first_customer_information_step_associates_visible_labels_with_inputs(self):
        for field_id in (
            "buyer1First", "buyer1Last", "buyer2", "buyer2Email", "seller1",
            "buyerMailAddr", "buyerPhone", "buyerEmail", "agentNameQuick",
            "agentLicenseQuick", "agentEmailQuick", "agentPhoneQuick",
            "agentBrokerageQuick", "agentBrokerLicenseQuick", "brokerFeeAmount",
            "brokerFeePercent",
        ):
            self.assertIn(f'for="{field_id}"', HTML)


if __name__ == "__main__":
    unittest.main()
