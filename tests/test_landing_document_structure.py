from pathlib import Path
import unittest


HTML = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class LandingDocumentStructureTests(unittest.TestCase):
    def test_interactive_offer_detail_surface_is_inside_the_document_body(self):
        body_start = HTML.index("<body>")
        detail_start = HTML.index('id="offerDetailBackdrop"')
        head_end = HTML.index("</head>")

        self.assertGreater(detail_start, body_start)
        self.assertGreater(detail_start, head_end)


if __name__ == "__main__":
    unittest.main()
