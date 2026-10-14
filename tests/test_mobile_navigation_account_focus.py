from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / 'index.html').read_text()


class MobileNavigationAccountFocusTests(unittest.TestCase):
    def test_trial_presentation_uses_existing_auth_refresh_without_changing_billing(self):
        result = subprocess.run(['node', '--test', str(ROOT/'tests/landing_trial_promo.runtime.cjs')],
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)

    def test_mobile_nav_can_wrap_long_actions_without_hiding_navigation(self):
        mobile = HTML.split('/* Mobile account/profile button fix */',1)[1].split('/* Admin operations dashboard */',1)[0]
        for rule in ('min-width:0', 'min-height:44px', 'white-space:normal',
                     '.nav-actions .nav-discovery { position:static;',
                     'width:min(220px,calc(100vw - 1.3rem))', '@media (max-width:360px)'):
            self.assertIn(rule, mobile)
        self.assertNotIn('display:none', mobile)
        self.assertIn('id="navCta" data-compact-label="Start →" aria-label="Build Your Offer →" onclick="beginOfferFrom(\'landing_nav_cta\')"',HTML)
        self.assertIn('id="accountCta" onclick="openAuthModal',HTML)
