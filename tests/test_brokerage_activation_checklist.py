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
        self.assertIn("continueBrokerageLaunch", HTML)
        self.assertIn("Continue: ", HTML)

    def test_launch_checklist_routes_to_the_earliest_unfinished_step(self):
        for target in (
            "brokerageBrandColor",
            "brokerageDefaultTitleCompany",
            "brokerageInviteEmail",
            "start_offer",
            "offers",
        ):
            with self.subTest(target=target):
                self.assertIn(f"target: '{target}'", HTML)
        self.assertIn("const nextActivationStep = activationSteps.find(step => !step.done)", HTML)
        self.assertIn('onclick="continueBrokerageLaunch(', HTML)
        self.assertIn("field.scrollIntoView({ behavior: 'smooth', block: 'center' })", HTML)

    def test_brokerage_admin_flags_active_access_with_pending_seat_as_activation_work(self):
        api = (Path(__file__).resolve().parents[1] / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
        self.assertIn('"membersAwaitingActivationWithActiveAccess"', api)
        self.assertIn('next_action = "Activate brokerage membership"', api)
        self.assertIn("membersAwaitingActivationWithActiveAccess", HTML)
        self.assertIn("Membership activation needed:", HTML)
        self.assertIn("? 'Activate' : 'Restore'", HTML)


if __name__ == "__main__":
    unittest.main()
