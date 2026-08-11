from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "supabase" / "migrations" / "20260811205736_redact_signwell_webhook_event_telemetry.sql"


class SignWellWebhookTelemetryRedactionMigrationTests(unittest.TestCase):
    def test_migration_only_redacts_historical_raw_unmatched_webhook_events(self):
        sql = MIGRATION.read_text(encoding="utf-8")
        self.assertIn("event_type = 'signwell_webhook_unmatched'", sql)
        self.assertIn("metadata ? 'raw'", sql)
        self.assertIn("'redacted', true", sql)
        self.assertIn("Historical SignWell webhook lifecycle event retained", sql)
        self.assertNotIn("delete from", sql.lower())
