from pathlib import Path
import unittest


HTML = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class ExpiredSigningRecoveryTests(unittest.TestCase):
    def test_expired_signwell_document_is_not_misclassified_as_generated(self):
        inactive = "if (status.includes('delete') || status.includes('expired') || status.includes('declined')) return 'inactive';"
        generated = "if (status.includes('generated') || status.includes('created') || hasDoc) return 'generated';"
        self.assertIn(inactive, HTML)
        self.assertIn(generated, HTML)
        self.assertLess(HTML.index(inactive, HTML.index('function bucketForOffer')), HTML.index(generated, HTML.index('function bucketForOffer')))

    def test_expired_packet_is_attention_worthy_with_a_safe_resend_handoff(self):
        self.assertIn("if (status.includes('expired')) return true;", HTML)
        self.assertIn("Signature link expired — duplicate into a new draft to resend", HTML)
        self.assertIn("Duplicate &amp; edit to resend", HTML)
        self.assertIn("duplicateOffer('${esc(o.id)}', false, true)", HTML)


if __name__ == "__main__":
    unittest.main()
