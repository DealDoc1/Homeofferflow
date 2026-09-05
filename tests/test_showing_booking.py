import unittest
from pathlib import Path


HTML = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class ShowingBookingTests(unittest.TestCase):
    def test_showing_checkout_receives_the_explicit_click_event(self):
        self.assertIn('onclick="bookShowing(event)"', HTML)
        self.assertIn('async function bookShowing(clickEvent)', HTML)
        self.assertIn('const btn = clickEvent?.currentTarget;', HTML)
        self.assertNotIn('const btn = event?.currentTarget;', HTML)


if __name__ == "__main__":
    unittest.main()
