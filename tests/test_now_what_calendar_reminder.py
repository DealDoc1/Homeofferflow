"""Regression coverage for the no-cost target-closing calendar reminder."""

from pathlib import Path
import unittest


HTML = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class NowWhatCalendarReminderTests(unittest.TestCase):
    def test_success_screen_has_a_hidden_calendar_action_until_a_closing_date_exists(self):
        self.assertIn('id="nowWhatCalendarAction" hidden', HTML)
        self.assertIn('calendarAction.hidden = !closing;', HTML)

    def test_calendar_reminder_is_local_download_not_an_external_service_call(self):
        self.assertIn('window.downloadClosingCalendarReminder', HTML)
        self.assertIn("'BEGIN:VCALENDAR'", HTML)
        self.assertIn("type: 'text/calendar;charset=utf-8'", HTML)
        self.assertIn("link.download = `homeofferflow-target-closing-", HTML)

    def test_calendar_reminder_validates_date_and_keeps_contract_confirmation_clear(self):
        self.assertIn('function nowWhatCalendarDate(value)', HTML)
        self.assertIn('Confirm the final date, time, and location from the fully signed contract.', HTML)
        self.assertIn('Confirm the final date, time, and location with the signed contract and title company.', HTML)


if __name__ == "__main__":
    unittest.main()
