import unittest
from pathlib import Path


class AiCalibrationReviewerPacketLauncherTests(unittest.TestCase):
    def test_admin_can_download_anonymized_reviewer_packet(self):
        source = Path('index.html').read_text()
        self.assertIn('downloadAiCalibrationReviewerPacket', source)
        self.assertIn('copyAiCalibrationReviewerInvite', source)
        self.assertIn('homeofferflow-ai-calibration-reviewer-packet.txt', source)
        for scenario in ('AI-CAL-01', 'AI-CAL-02', 'AI-CAL-03', 'AI-CAL-04', 'AI-CAL-05'):
            self.assertIn(scenario, source)
        self.assertIn('Generated review output is not calibration evidence by itself.', source)
        self.assertIn('Download reviewer packet', source)
        self.assertIn('missingScenarios', source)
        self.assertIn('JSON.stringify(missingCalibrationIds)', source)


if __name__ == '__main__':
    unittest.main()
