from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = spec_from_file_location(
    "release_preflight", ROOT / "scripts" / "release_preflight.py"
)
release_preflight = module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(release_preflight)


class ReleasePreflightTests(unittest.TestCase):
    def _completed_evidence(self) -> str:
        return """
Approved source: TXR form revision approved by brokerage.
Authorization: broker confirmed authorized use.
Signing plan: buyer and agent roles documented.
Rendered signed-PDF QA: completed packet visually reviewed.
Regression: dedicated golden scenario and buyer offer suite passed.
Release authority: product reviewer approved the release copy.
"""

    def test_non_packet_change_does_not_require_form_evidence(self):
        result = release_preflight.main(["--changed-file", "index.html"])
        self.assertEqual(result, 0)

    def test_packet_change_fails_closed_without_evidence(self):
        result = release_preflight.main(["--changed-file", "api/fill-pdf.py"])
        self.assertEqual(result, 2)

    def test_packet_change_accepts_completed_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            evidence = Path(directory) / "buyer-rep.md"
            evidence.write_text(self._completed_evidence())
            result = release_preflight.main(
                [
                    "--changed-file",
                    "api/fill-pdf.py",
                    "--evidence-file",
                    str(evidence),
                ]
            )
        self.assertEqual(result, 0)

    def test_packet_change_rejects_template_placeholders(self):
        with tempfile.TemporaryDirectory() as directory:
            evidence = Path(directory) / "buyer-rep.md"
            evidence.write_text(
                self._completed_evidence() + "\nApproved public-facing scope: [fill this in]\n"
            )
            result = release_preflight.main(
                [
                    "--changed-file",
                    "20-19_0.pdf",
                    "--evidence-file",
                    str(evidence),
                ]
            )
        self.assertEqual(result, 2)

    def test_expected_deploy_author_accepts_the_matching_commit_author(self):
        with patch.object(
            release_preflight, "_git_commit_author_email", return_value="andrewchri@gmail.com"
        ):
            result = release_preflight.main(
                [
                    "--changed-file",
                    "index.html",
                    "--expected-deploy-author-email",
                    "andrewchri@gmail.com",
                ]
            )
        self.assertEqual(result, 0)

    def test_expected_deploy_author_rejects_a_non_member_author(self):
        with patch.object(
            release_preflight, "_git_commit_author_email", return_value="agent@brokerage.com"
        ):
            result = release_preflight.main(
                [
                    "--changed-file",
                    "index.html",
                    "--expected-deploy-author-email",
                    "andrewchri@gmail.com",
                ]
            )
        self.assertEqual(result, 2)


if __name__ == "__main__":
    unittest.main()
