import tempfile
import unittest
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader
from reportlab.pdfgen.canvas import Canvas

from scripts.qa.build_remaining_signwell_release_qa import (
    FORM_ORDER,
    QA_RECIPIENTS,
    build_packet,
    build_payload,
    form_fields,
    qa_recipient,
    render_form,
    sample_for,
)


ROOT = Path(__file__).resolve().parents[1]


def write_blank_form(path: Path, pages: int) -> None:
    canvas = Canvas(str(path), pagesize=(612, 792))
    for _ in range(pages):
        canvas.showPage()
    canvas.save()


def synthetic_sources(directory: str) -> Path:
    source_dir = Path(directory)
    for code in FORM_ORDER:
        write_blank_form(source_dir / f"TXR{code}.pdf", 6 if code == "1506" else 1)
    (source_dir / "lead_based_paint_56-0.pdf").write_bytes(
        (ROOT / "lead_based_paint_56-0.pdf").read_bytes()
    )
    return source_dir


class RemainingSignwellReleaseQaTests(unittest.TestCase):
    def test_recipient_mapping_preserves_second_party_separation(self):
        self.assertEqual(qa_recipient("1"), "qa_a")
        self.assertEqual(qa_recipient("3"), "qa_a")
        self.assertEqual(qa_recipient("associate"), "qa_a")
        self.assertEqual(qa_recipient("2"), "qa_b")
        self.assertEqual(qa_recipient("4"), "qa_b")

    def test_standalone_geometry_is_shifted_without_resizing(self):
        page_offset = 9
        with tempfile.TemporaryDirectory() as directory:
            sources = synthetic_sources(directory)
            for code in FORM_ORDER:
                with self.subTest(code=code):
                    data, brokerage, associate = sample_for(code)
                    source = (sources / f"TXR{code}.pdf").read_bytes()
                    rendered = render_form(source, code, data, brokerage, associate)
                    local = form_fields(code, data, len(PdfReader(BytesIO(rendered)).pages))
                    self.assertTrue(local)
                    for field in local:
                        shifted = {**field, "page": field["page"] + page_offset}
                        self.assertEqual(shifted["page"] - page_offset, field["page"])
                        for key in ("type", "x", "y", "width", "height", "required"):
                            self.assertEqual(shifted[key], field[key])

    def test_packet_covers_every_remaining_scope_with_unique_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            packet, grouped_fields, manifest = build_packet(synthetic_sources(directory))
        reader = PdfReader(BytesIO(packet))
        fields = grouped_fields[0]
        self.assertEqual([item["form_code"] for item in manifest], [
            "PURCHASE-MAX-COVERAGE", "TXR-1506", "TXR-1508",
            "TXR-1948", "TXR-1953", "TXR-1954",
        ])
        self.assertEqual(manifest[-1]["end_page"], len(reader.pages))
        self.assertEqual(len({field["api_id"] for field in fields}), len(fields))
        self.assertEqual({field["recipient_id"] for field in fields}, {"qa_a", "qa_b"})
        self.assertTrue(any("trec48_1" in field["api_id"] for field in fields))
        self.assertTrue(any("txr1948" in field["api_id"] for field in fields))
        purchase_text = "\n".join(
            reader.pages[index].extract_text() or ""
            for index in range(manifest[0]["start_page"] - 1, manifest[0]["end_page"])
        )
        self.assertIn("AUTHORIZING HYDROSTATIC TESTING", purchase_text)
        self.assertIn("LEAD-BASED PAINT", purchase_text.upper())

    def test_payload_is_parallel_nonbinding_and_uses_only_approved_inboxes(self):
        payload = build_payload(b"packet", [[{
            "api_id": "field", "type": "signature", "page": 1,
            "x": 1, "y": 1, "width": 10, "height": 10,
            "recipient_id": "qa_a", "required": True,
        }]])
        self.assertTrue(payload["test_mode"])
        self.assertFalse(payload["draft"])
        self.assertFalse(payload["apply_signing_order"])
        self.assertFalse(payload["reminders"])
        self.assertEqual(
            {recipient["email"] for recipient in payload["recipients"]},
            {"andrewchri@gmail.com", "brewbqinfo@gmail.com"},
        )
        self.assertEqual(payload["recipients"], QA_RECIPIENTS)

    def test_missing_private_source_fails_before_provider_call(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FileNotFoundError):
                build_packet(Path(directory))


if __name__ == "__main__":
    unittest.main()
