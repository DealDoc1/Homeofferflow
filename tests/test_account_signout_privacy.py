from pathlib import Path
import unittest


HTML = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class AccountSignOutPrivacyTests(unittest.TestCase):
    def test_signout_clears_cached_account_data_and_closes_private_views(self):
        start = HTML.index("async function signOutAccount()")
        end = HTML.index("async function initSupabaseAuth()", start)
        signout = HTML[start:end]

        for expected in (
            "hofAuth.myOffers = [];",
            "hofAuth.subscription = null;",
            "hofAuth.usage = null;",
            "hofAuth.accountProfile = null;",
            "localStorage.setItem('hof_offer_draft_owner', signedOutUserId);",
            "closeAccountDashboard();",
            "closeOfferDetail();",
        ):
            self.assertIn(expected, signout)

    def test_signout_preserves_unsynced_draft_but_binds_it_to_the_same_account(self):
        start = HTML.index("function saveDraftNow()")
        end = HTML.index("function scheduleDraftSave()", start)
        saver = HTML[start:end]
        self.assertIn("const HOF_STORAGE_OWNER_KEY = 'hof_offer_draft_owner';", HTML)
        self.assertIn("localStorage.setItem(HOF_STORAGE_OWNER_KEY, ownerUserId);", saver)

        start = HTML.index("function restoreDraft()")
        end = HTML.index("function refreshSelectedRadioCards()", start)
        restore = HTML[start:end]
        self.assertIn("ownerUserId && ownerUserId !== currentUserId", restore)
        self.assertIn("if (!window.__hofDraftRestoreAuthReady) return false;", restore)
        self.assertIn("different signed-in account", restore)
        self.assertNotIn("localStorage.removeItem(HOF_STORAGE_KEY)", restore)

        init_start = HTML.index("async function initSupabaseAuth()")
        init_end = HTML.index("function isProfileMeaningful", init_start)
        init = HTML[init_start:init_end]
        self.assertIn("window.__hofDraftRestoreAuthReady = true;", init)
        self.assertIn("ownerUserId === (hofAuth.session?.user?.id || '')", init)

    def test_signout_does_not_clear_cached_state_when_supabase_rejects_signout(self):
        start = HTML.index("async function signOutAccount()")
        end = HTML.index("async function initSupabaseAuth()", start)
        signout = HTML[start:end]
        self.assertIn("const { error } = await client.auth.signOut();", signout)
        self.assertLess(signout.index("if (error)"), signout.index("hofAuth.session = null;"))


if __name__ == "__main__":
    unittest.main()
