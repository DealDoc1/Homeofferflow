from pathlib import Path
import unittest


INDEX = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class WizardEmailValidationTests(unittest.TestCase):
    def test_required_signing_and_agent_email_inputs_use_native_email_hints(self):
        for expected in (
            'id="buyerEmail" name="buyerEmail" inputmode="email" autocomplete="email"',
            'id="buyer2Email" inputmode="email" autocomplete="email"',
            'id="agentEmailQuick" inputmode="email" autocomplete="email"',
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, INDEX)

    def test_step_one_blocks_invalid_buyer_cobuyer_and_agent_email_addresses(self):
        start = INDEX.index("function validateCurrentStep()")
        end = INDEX.index("function startHomebuyerOffer()", start)
        validation = INDEX[start:end]
        self.assertIn("function requireValidEmail(id, label, missing)", INDEX)
        self.assertIn("el.checkValidity()", INDEX)
        self.assertIn("requireValidEmail('buyerEmail', 'valid buyer email', missing);", validation)
        self.assertIn("requireValidEmail('buyer2Email', 'valid co-buyer email', missing);", validation)
        self.assertIn("requireValidEmail('agentEmailQuick', 'valid agent email', missing);", validation)


if __name__ == "__main__":
    unittest.main()
