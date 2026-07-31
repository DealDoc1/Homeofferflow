from pathlib import Path
import unittest


class ConsumerShowingCheckoutSafetyTests(unittest.TestCase):
    def test_unfulfilled_showing_booking_is_not_exposed_in_consumer_wizard(self):
        source = Path("index.html").read_text(encoding="utf-8")
        self.assertNotIn("SHOWING_BOOKING_PRICE_ID", source)
        self.assertNotIn("Book Showing — $50", source)
        self.assertNotIn("plan: 'showing-booking'", source)
        self.assertIn("I'll arrange a viewing before continuing", source)


if __name__ == "__main__":
    unittest.main()
