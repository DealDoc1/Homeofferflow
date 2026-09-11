"""Guard keyboard continuity across the four transaction question paths."""

from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class AgentInterviewNavigationTests(unittest.TestCase):
    def test_purchase_choices_keep_relevant_help_without_repeating_shared_instructions(self):
        html = (ROOT / 'index.html').read_text(encoding='utf-8')
        start = html.index(": type === 'purchase_addendum'")
        end = html.index("{ label: 'Showing Form'", start)
        choices = html[start:end]
        self.assertNotIn('Answer the guided questions, review the completed addendum', choices)
        self.assertIn('For a purchase involving existing tenant leases.', choices)
        self.assertIn('For a purchase involving leased fixtures, such as solar panels.', choices)
        for guidance in (
            'seller will finance all or part of the price',
            'buyer will assume the seller’s existing loan',
            'specific environmental review rights',
            'appraisal-related termination or waiver choice',
            'seller will reserve mineral interests',
        ):
            self.assertIn(guidance, choices)
        for form in ['1914', '1919', '1917', '1948', '1953', '1954', '1905']:
            self.assertIn(f"formCode: 'TXR-{form}'", choices)

    def test_main_and_nested_questions_share_the_original_return_target(self):
        html = (ROOT / 'index.html').read_text(encoding='utf-8')
        start = html.index('window.hofOpenAgentPackageInterview = function')
        end = html.index('// The agent workspace begins with the transaction', start)
        interview = html[start:end]
        self.assertEqual(interview.count('const returnFocus ='), 1)
        self.assertIn("bindPackageQuestionKeys(modal, () => closeInterview('escape'));", interview)
        self.assertIn("bindPackageQuestionKeys(followUp, () => closeFollowUp('escape'));", interview)
        back = interview.split('const returnToPackageQuestion = () => {', 1)[1].split('};', 1)[0]
        self.assertLess(back.index('restorePackageFocus();'), back.index('window.hofOpenAgentPackageInterview'))

    @unittest.skipUnless(shutil.which('node'), 'Node.js is required for keyboard runtime tests')
    def test_actual_keyboard_and_return_focus_handlers(self):
        result = subprocess.run(
            ['node', '--test', str(Path(__file__).with_name('agent_interview_navigation.runtime.cjs'))],
            capture_output=True, text=True, timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
