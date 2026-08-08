from pathlib import Path
import unittest


HTML = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class AiCalibrationPacketDownloadTests(unittest.TestCase):
    def test_review_ui_can_download_the_same_anonymized_packet_it_can_copy(self):
        self.assertIn("buildAiCalibrationPacket", HTML)
        self.assertIn("downloadAiCalibrationPacket", HTML)
        self.assertIn("homeofferflow-ai-calibration-packet.txt", HTML)
        self.assertIn("Download Calibration Packet", HTML)
        self.assertIn("Remove private details before sharing.", HTML)


if __name__ == "__main__":
    unittest.main()
