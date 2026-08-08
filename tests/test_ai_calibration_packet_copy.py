from pathlib import Path
import unittest


HTML = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class AiCalibrationPacketCopyTests(unittest.TestCase):
    def test_review_ui_exposes_privacy_safe_calibration_packet_copy(self):
        self.assertIn("copyAiCalibrationPacket", HTML)
        self.assertIn("Copy Calibration Packet", HTML)
        self.assertIn("Do not add names, exact addresses, MLS numbers", HTML)
        self.assertIn("Reviewer assessment:", HTML)


if __name__ == "__main__":
    unittest.main()
