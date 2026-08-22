from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")


class FsboEmailReturnSubmitTests(unittest.TestCase):
    def test_email_field_uses_a_mobile_send_key_and_explains_the_low_commitment_action(self):
        self.assertIn('id="fsboSellerEmail" type="email" inputmode="email" enterkeyhint="send"', HTML)
        self.assertIn('id="fsboSellerEmailHelp"', HTML)
        self.assertIn('press Return/Go or use the button below.', HTML)

    def test_enter_on_email_submits_only_after_the_existing_two_field_validation_passes(self):
        self.assertIn("document.getElementById('fsboSellerEmail')?.addEventListener('keydown'", HTML)
        self.assertIn("event.key !== 'Enter' || event.isComposing || !fsboRequiredFieldsReady()", HTML)
        self.assertIn("window.submitFsboSellerLead?.('email_enter');", HTML)
        self.assertIn("Google Places consume Enter when selecting a suggestion.", HTML)
        self.assertIn("function fsboRequiredFieldsReady()", HTML)
        self.assertIn("function fsboSubmissionKey(payload)", HTML)


if __name__ == "__main__":
    unittest.main()
