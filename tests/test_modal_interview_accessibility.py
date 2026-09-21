from pathlib import Path
import unittest


HTML = (Path(__file__).resolve().parents[1] / 'index.html').read_text(encoding='utf-8')


class ModalInterviewAccessibilityTests(unittest.TestCase):
    def test_guided_offer_interview_is_an_isolated_dialog(self):
        self.assertIn(
            '<div class="wizard-overlay" id="wizardOverlay" role="dialog" aria-modal="true" '
            'aria-label="Guided offer interview" aria-hidden="true" tabindex="-1" data-nosnippet>',
            HTML,
        )
        open_start = HTML.index('function openWizard(')
        open_end = HTML.index('\n  function closeWizard()', open_start)
        open_flow = HTML[open_start:open_end]
        self.assertIn("wizard.setAttribute('aria-hidden', 'false')", open_flow)
        self.assertIn('window.setHofModalIsolation?.(wizard, true)', open_flow)
        self.assertIn("wizard.focus({ preventScroll: true })", open_flow)

        close_start = HTML.index('function returnHomeFromWizard()')
        close_end = HTML.index('\n  function startNewOffer()', close_start)
        close_flow = HTML[close_start:close_end]
        self.assertIn("overlay.setAttribute('aria-hidden', 'true')", close_flow)
        self.assertIn('window.setHofModalIsolation?.(overlay, false)', close_flow)

    def test_every_primary_customer_dialog_uses_shared_isolation(self):
        regions = {
            'account': ('async function openAccountDashboard(', 'function getBillingMonth(', 2),
            'feedback': ('function openBetaFeedback()', 'async function submitBetaFeedback()', 2),
            'fsbo': ('window.openFsboSellerModal = function()', 'function fsboVal(', 2),
            'partner': ('window.openFoundingPartnerModal = function', 'window.submitFoundingPartnerLead = async function', 2),
        }
        for name, (start_marker, end_marker, minimum) in regions.items():
            with self.subTest(path=name):
                start = HTML.index(start_marker)
                end = HTML.index(end_marker, start)
                region = HTML[start:end]
                self.assertGreaterEqual(region.count('window.setHofModalIsolation?.('), minimum)

        self.assertGreaterEqual(HTML.count('window.setHofModalIsolation?.(modal, true)'), 5)
        self.assertIn('window.setHofModalIsolation?.(modal, false)', HTML)


if __name__ == '__main__':
    unittest.main()
