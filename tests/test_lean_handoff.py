from pathlib import Path
from tempfile import TemporaryDirectory
import subprocess
import unittest


from scripts import build_lean_handoff


class LeanHandoffTests(unittest.TestCase):
    def _git(self, root: Path, *args: str) -> None:
        subprocess.run(
            ["git", *args],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )

    def test_handoff_uses_live_repository_state_and_batch_contract(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self._git(root, "init", "-b", "codex/test-batch")
            self._git(root, "config", "user.email", "test@example.test")
            self._git(root, "config", "user.name", "HomeOfferFlow Test")
            (root / "tracked.txt").write_text("initial\n", encoding="utf-8")
            self._git(root, "add", "tracked.txt")
            self._git(root, "commit", "-m", "Initial evidence")
            (root / "tracked.txt").write_text("changed\n", encoding="utf-8")

            handoff = build_lean_handoff.build_handoff(
                root=root,
                outcome="Make checkout recovery clear.",
                scope="Checkout return card and focused tests.",
                production_revision="abc123",
                cost_constraint="No preview deployment.",
                evidence="Focused tests and a mobile browser check.",
            )

            self.assertIn("Intended user outcome: Make checkout recovery clear.", handoff)
            self.assertIn("Exact scope: Checkout return card and focused tests.", handoff)
            self.assertIn("Authoritative production revision: abc123", handoff)
            self.assertIn("Cost/release constraint: No preview deployment.", handoff)
            self.assertIn("Completion evidence required: Focused tests and a mobile browser check.", handoff)
            self.assertIn("Branch: `codex/test-batch`", handoff)
            self.assertIn("M tracked.txt", handoff)
            self.assertIn("Initial evidence", handoff)

    def test_long_repository_sections_are_bounded(self):
        lines, omitted = build_lean_handoff._bounded_lines(
            "\n".join(f"line-{index}" for index in range(25)), 8
        )
        self.assertEqual(len(lines), 8)
        self.assertEqual(omitted, 17)
        self.assertIn("…and 17 more", "\n".join(build_lean_handoff._bullet_lines(lines, omitted, "clean")))

    def test_contract_values_are_one_line_and_size_bounded(self):
        self.assertEqual(
            build_lean_handoff._contract_value("  one\n  bounded   fact  "),
            "one bounded fact",
        )
        with self.assertRaises(ValueError):
            build_lean_handoff._contract_value("   ")
        with self.assertRaises(ValueError):
            build_lean_handoff._contract_value("x" * 501)


if __name__ == "__main__":
    unittest.main()
