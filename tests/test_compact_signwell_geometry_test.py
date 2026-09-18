import io
import tempfile
import unittest
from pathlib import Path

from pypdf import PdfReader
from reportlab.pdfgen.canvas import Canvas

from scripts.qa import build_compact_signwell_geometry_test as qa


def blank_pdf(pages):
    output = io.BytesIO()
    canvas = Canvas(output, pagesize=(612, 792))
    for _ in range(pages):
        canvas.showPage()
    canvas.save()
    return output.getvalue()


class CompactSignWellGeometryTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.source_dir = Path(self.temp.name)
        for code, pages in {"1501": 6, "1507": 2, "1905": 1, "1914": 2, "1917": 1, "1919": 2}.items():
            (self.source_dir / f"TXR{code}.pdf").write_bytes(blank_pdf(pages))

    def tearDown(self):
        self.temp.cleanup()

    def test_combines_every_pending_map_without_changing_local_geometry(self):
        packet, grouped_fields, manifest = qa.build_packet(self.source_dir)
        fields = grouped_fields[0]
        self.assertEqual(len(PdfReader(io.BytesIO(packet)).pages), 14)
        self.assertEqual([entry["form_code"] for entry in manifest], [f"TXR-{code}" for code in qa.FORM_ORDER])
        self.assertEqual([(entry["start_page"], entry["end_page"]) for entry in manifest],
                         [(1, 6), (7, 8), (9, 9), (10, 11), (12, 12), (13, 14)])
        self.assertEqual({field["recipient_id"] for field in fields}, {"qa_a", "qa_b"})
        self.assertEqual(len({field["api_id"] for field in fields}), len(fields))

        offset = 0
        by_id = {field["api_id"]: field for field in fields}
        for code, entry in zip(qa.FORM_ORDER, manifest):
            data, _, _ = qa.sample_for(code)
            page_count = entry["end_page"] - entry["start_page"] + 1
            local = qa.form_fields(code, data, page_count)
            for field in local:
                combined = by_id[field["api_id"]]
                for key in ("type", "x", "y", "width", "height", "required"):
                    self.assertEqual(combined[key], field[key], (code, field["api_id"], key))
                self.assertEqual(combined["page"], field["page"] + offset)
                self.assertEqual(combined["recipient_id"], qa.qa_recipient(field["recipient_id"]))
            offset = entry["end_page"]

    def test_payload_is_nonbinding_parallel_and_uses_only_approved_qa_addresses(self):
        packet, fields, _ = qa.build_packet(self.source_dir)
        payload = qa.build_payload(packet, fields)
        self.assertTrue(payload["test_mode"])
        self.assertFalse(payload["draft"])
        self.assertFalse(payload["apply_signing_order"])
        self.assertFalse(payload["reminders"])
        self.assertEqual(
            {recipient["email"] for recipient in payload["recipients"]},
            {"andrewchri@gmail.com", "brewbqinfo@gmail.com"},
        )
        self.assertEqual(payload["fields"], fields)

    def test_missing_source_stops_before_packet_creation(self):
        (self.source_dir / "TXR1917.pdf").unlink()
        with self.assertRaisesRegex(FileNotFoundError, "TXR1917.pdf"):
            qa.build_packet(self.source_dir)


if __name__ == "__main__":
    unittest.main()
