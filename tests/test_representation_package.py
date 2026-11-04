import io
import unittest

from pypdf import PdfReader
from reportlab.pdfgen.canvas import Canvas

from lib.representation_package import compose_representation_package


def pdf(label, pages):
    output = io.BytesIO()
    canvas = Canvas(output, pagesize=(612, 792))
    for page in range(pages):
        canvas.drawString(36, 740, f"{label} {page + 1}")
        canvas.showPage()
    canvas.save()
    return output.getvalue()


def fields(prefix, recipient="1", pages=1):
    return [[{"api_id": f"{prefix}_signature_{page}", "type": "signature",
              "recipient_id": recipient, "page": page, "x": 72, "y": 800,
              "width": 200, "height": 24, "required": True}
             for page in range(1, pages + 1)]]


class RepresentationPackageTests(unittest.TestCase):
    def test_selected_notice_is_appended_and_its_signer_fields_are_offset(self):
        result = compose_representation_package(
            pdf("QA representation", 3), fields("representation", pages=3),
            pdf("QA consumer notice", 6), fields("notice", pages=6),
            recipients=["1", "associate"],
        )
        reader = PdfReader(io.BytesIO(result.pdf))
        self.assertEqual(len(reader.pages), 9)
        self.assertIn("QA representation 1", reader.pages[0].extract_text())
        self.assertIn("QA consumer notice 1", reader.pages[3].extract_text())
        self.assertEqual(result.manifest, {
            "primary_pages": 3, "related_code": "TXR-1506",
            "related_start_page": 4, "related_end_page": 9,
            "included_codes": ["TXR-1506"], "page_count": 9, "field_count": 9,
        })
        self.assertEqual([field["page"] for field in result.fields[0]],
                         [1, 2, 3, 4, 5, 6, 7, 8, 9])
        self.assertTrue(all(field["api_id"].startswith("txr1506_")
                            for field in result.fields[0][3:]))

    def test_invalid_sources_fields_and_unconfirmed_signers_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "not available"):
            compose_representation_package(pdf("p", 1), fields("p"), pdf("r", 1),
                                           fields("r"), recipients=["1"], related_code="TXR-1508")
        with self.assertRaisesRegex(ValueError, "unreviewed signer"):
            compose_representation_package(pdf("p", 1), fields("p", "broker"),
                                           pdf("r", 1), fields("r"), recipients=["1"])
        with self.assertRaisesRegex(ValueError, "outside its document"):
            compose_representation_package(pdf("p", 1), fields("p"), pdf("r", 1),
                                           fields("r", pages=2), recipients=["1"])

    def test_saved_iabs_is_appended_as_information_only_after_notice(self):
        result = compose_representation_package(
            pdf("QA representation", 2), fields("representation", pages=2),
            pdf("QA notice", 1), fields("notice"), recipients=["1"],
            information_documents=[("IABS", pdf("QA agent IABS", 2))],
        )
        reader = PdfReader(io.BytesIO(result.pdf))
        self.assertEqual(len(reader.pages), 5)
        self.assertIn("QA notice", reader.pages[2].extract_text())
        self.assertIn("QA agent IABS", reader.pages[3].extract_text())
        self.assertEqual(result.fields[0], fields("representation", pages=2)[0] +
                         [{**field, "api_id": "txr1506_" + field["api_id"], "page": field["page"] + 2}
                          for field in fields("notice")[0]])
        self.assertEqual(result.manifest["included_codes"], ["TXR-1506", "IABS"])
        self.assertEqual((result.manifest["iabs_start_page"], result.manifest["iabs_end_page"]), (4, 5))

    def test_iabs_only_package_has_no_client_signing_fields(self):
        result = compose_representation_package(
            pdf("QA representation", 2), fields("representation", pages=2),
            recipients=["1"], information_documents=[("IABS", pdf("QA agent IABS", 1))],
        )
        self.assertEqual(len(PdfReader(io.BytesIO(result.pdf)).pages), 3)
        self.assertEqual(len(result.fields[0]), 2)
        self.assertEqual(result.manifest["included_codes"], ["IABS"])
        with self.assertRaisesRegex(ValueError, "not available"):
            compose_representation_package(pdf("p", 1), fields("p"), recipients=["1"],
                                           information_documents=[("TXR-1506", pdf("x", 1))])

if __name__ == "__main__":
    unittest.main()
