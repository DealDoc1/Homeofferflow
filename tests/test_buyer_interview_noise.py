"""Regression coverage for keeping optional buyer planning tools out of the core interview."""

from pathlib import Path
import unittest


HTML = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class BuyerInterviewNoiseTests(unittest.TestCase):
    def test_payment_estimate_is_an_optional_collapsed_planning_tool(self):
        start = HTML.index('<details class="payment-calc-card" id="paymentCalcCard">')
        end = HTML.index('</details>', start)
        calculator = HTML[start:end]

        self.assertIn('<summary>Estimate monthly payment <span>Optional planning tool</span></summary>', calculator)
        self.assertIn('It does not change your offer terms.', calculator)
        self.assertNotIn(' open', HTML[start:start + 60])
        self.assertIn('id="calcInterestRate"', calculator)
        self.assertIn('id="calcCashToClose"', calculator)


if __name__ == "__main__":
    unittest.main()
