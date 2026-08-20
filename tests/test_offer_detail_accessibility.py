from pathlib import Path
import unittest


HTML = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class OfferDetailAccessibilityTests(unittest.TestCase):
    def test_offer_detail_is_a_labelled_modal_dialog(self):
        markup_start = HTML.index('<div class="offer-detail-backdrop" id="offerDetailBackdrop"')
        markup_end = HTML.index('</div>\n<nav>', markup_start)
        markup = HTML[markup_start:markup_end]

        self.assertIn('aria-hidden="true"', markup)
        self.assertIn('role="dialog"', markup)
        self.assertIn('aria-modal="true"', markup)
        self.assertIn('aria-labelledby="offerDetailTitle"', markup)
        self.assertIn('id="offerDetailTitle"', markup)
        self.assertIn('id="offerDetailClose"', markup)
        self.assertIn('aria-label="Close offer details"', markup)

    def test_offer_detail_restores_focus_and_supports_escape(self):
        close_start = HTML.index('window.closeOfferDetail = function()')
        close_end = HTML.index('\n\n  function offerField', close_start)
        controls = HTML[close_start:close_end]

        self.assertIn("backdrop.setAttribute('aria-hidden', 'true')", controls)
        self.assertIn('window.__hofOfferDetailReturnFocus', controls)
        self.assertIn('returnFocus.focus()', controls)
        self.assertIn("event.key === 'Escape'", controls)
        self.assertIn("window.closeOfferDetail()", controls)

    def test_current_workspace_detail_announces_modal_and_receives_focus(self):
        start = HTML.index('root.viewOfferDetails = async function(offerId)')
        end = HTML.index('\n  };', start)
        detail = HTML[start:end]

        self.assertIn('root.__hofOfferDetailReturnFocus = document.activeElement', detail)
        self.assertIn("backdrop.setAttribute('aria-hidden', 'false')", detail)
        self.assertIn("document.getElementById('offerDetailClose')?.focus()", detail)


if __name__ == '__main__':
    unittest.main()
