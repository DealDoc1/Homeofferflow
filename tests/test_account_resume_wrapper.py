import unittest
from pathlib import Path


class AccountResumeWrapperTests(unittest.TestCase):
    def test_global_resume_wrapper_keeps_the_role_aware_implementation(self):
        source = Path('index.html').read_text()
        self.assertIn(
            'const resumeLocalAccountOfferDraftForRole = resumeLocalAccountOfferDraft;',
            source,
        )
        wrapper = source[source.index('window.resumeLocalAccountOfferDraft = function()'):source.index('function refreshResumeOfferCtas()')]
        self.assertIn('return resumeLocalAccountOfferDraftForRole(role);', wrapper)
        self.assertNotIn('return resumeLocalAccountOfferDraft(role);', wrapper)


if __name__ == '__main__':
    unittest.main()
