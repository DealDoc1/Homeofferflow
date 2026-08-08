import unittest
from pathlib import Path


class AiCalibrationDispositionMetricTests(unittest.TestCase):
    def test_server_counts_only_calibration_dispositions(self):
        source = Path('api/admin-dashboard.py').read_text()
        self.assertIn('ai_calibration_dispositions', source)
        self.assertIn('aiCalibrationDispositionCounts', source)
        self.assertIn('aiCalibrationScenarioDispositionCounts', source)
        self.assertIn('reviewer disposition: {disposition}', source)

    def test_admin_dashboard_surfaces_disposition_totals(self):
        source = Path('index.html').read_text()
        self.assertIn('calibrationDispositions', source)
        self.assertIn('calibrationScenarioSummary', source)
        self.assertIn('Disposition: keep', source)
        self.assertIn('revise', source)
        self.assertIn('remove', source)


if __name__ == '__main__':
    unittest.main()
