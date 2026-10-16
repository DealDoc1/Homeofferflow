from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class InsurancePartnersRuntimeTests(unittest.TestCase):
    def test_actual_insurance_renderer(self):
        result = subprocess.run(['node', '--test', str(ROOT / 'tests/insurance_partners.runtime.cjs')], capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_placement_is_inside_optional_planner_and_cached_shell(self):
        html = (ROOT / 'index.html').read_text()
        planner = html[html.index('<details class="payment-calc-card"'):]
        self.assertIn('id="hofInsurancePartners"', planner[:planner.index('</details>')])
        self.assertIn('/assets/insurance-partners.js', html)
        self.assertIn('/assets/insurance-partners.js', (ROOT / 'service-worker.js').read_text())
        self.assertIn('"insurance_planning"', (ROOT / 'api/fsbo-lead.py').read_text())


if __name__ == '__main__':
    unittest.main()
