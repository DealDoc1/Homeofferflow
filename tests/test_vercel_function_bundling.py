import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))


class VercelFunctionBundlingTests(unittest.TestCase):
    def test_python_functions_exclude_non_runtime_project_content(self):
        python_functions = [
            "api/admin-dashboard.py",
            "api/ai-offer-review.py",
            "api/create-billing-portal/index.py",
            "api/create-subscription-checkout/index.py",
            "api/feedback-alert/index.py",
            "api/fill-pdf.py",
            "api/fsbo-lead.py",
            "api/signwell-webhook.py",
            "api/stripe-webhook/index.py",
            "api/submit-feedback/index.py",
        ]
        for function in python_functions:
            excluded = CONFIG["functions"][function]["excludeFiles"]
            for path in ("tests/**", "docs/**", "assets/**", "supabase/**", "scripts/**", "**/*.pyc"):
                self.assertIn(path, excluded, function)

    def test_node_functions_exclude_non_runtime_project_content(self):
        excluded = CONFIG["functions"]["api/*.js"]["excludeFiles"]
        for path in ("tests/**", "docs/**", "assets/**", "supabase/**", "scripts/**", "**/*.pyc"):
            self.assertIn(path, excluded)

    def test_pdf_packet_function_keeps_required_runtime_sources(self):
        config = CONFIG["functions"]["api/fill-pdf.py"]
        self.assertIn("buyer_temporary_residential_lease_16-7.pdf", config["includeFiles"])
        self.assertIn("seller_temporary_residential_lease_15-7.pdf", config["includeFiles"])
        self.assertIn("tests/**", config["excludeFiles"])
