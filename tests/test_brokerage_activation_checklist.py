from pathlib import Path
import unittest


HTML = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class BrokerageActivationChecklistTests(unittest.TestCase):
    def test_brokerage_admin_surface_exposes_metric_driven_launch_checklist(self):
        self.assertIn("Team launch checklist", HTML)
        self.assertIn("Set brokerage branding", HTML)
        self.assertIn("Add shared title defaults", HTML)
        self.assertIn("Invite or connect an agent", HTML)
        self.assertIn("Create the first offer", HTML)
        self.assertIn("Send the first packet for signing", HTML)
        self.assertIn("activationComplete", HTML)
        self.assertIn("Continue launch", HTML)


if __name__ == "__main__":
    unittest.main()
