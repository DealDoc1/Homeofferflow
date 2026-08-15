from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = (ROOT / "requirements.txt").read_text(encoding="utf-8")
TEST = (ROOT / "requirements-test.txt").read_text(encoding="utf-8")


class RuntimeDependencyScopeTests(unittest.TestCase):
    def test_runtime_dependencies_are_pinned_for_reproducible_deployments(self):
        packages = [line.strip() for line in RUNTIME.splitlines() if line.strip() and not line.startswith("#")]
        self.assertTrue(packages)
        self.assertTrue(all("==" in package for package in packages), packages)

    def test_pdf_geometry_inspector_is_test_only(self):
        self.assertNotIn("pdfplumber", RUNTIME)
        self.assertIn("pdfplumber==0.11.9", TEST)
        self.assertIn("-r requirements.txt", TEST)

    def test_each_python_ci_workflow_installs_test_dependencies(self):
        for filename in (
            "test.yml",
            "release-gate.yml",
            "production-release.yml",
        ):
            workflow = (ROOT / ".github" / "workflows" / filename).read_text(encoding="utf-8")
            self.assertIn("--requirement requirements-test.txt", workflow, filename)


if __name__ == "__main__":
    unittest.main()
