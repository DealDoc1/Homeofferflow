import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")


class CustomerWorkspaceLanguageTests(unittest.TestCase):
    def test_broker_workspace_uses_operating_language_not_build_language(self):
        self.assertIn("<h4>Broker Workspace</h4>", HTML)
        self.assertIn("Use this checklist to set up repeatable broker and team work.", HTML)
        self.assertNotIn("Broker role foundation", HTML)
        self.assertNotIn("before wider broker/team rollout", HTML)

    def test_restricted_form_status_is_clear_without_internal_foundation_jargon(self):
        self.assertIn("Status only — this does not activate sending or signing.", HTML)
        self.assertNotIn("private-draft foundation", HTML)

    def test_agent_forms_explain_review_before_available_sending(self):
        self.assertIn("Review your prepared documents here.", HTML)
        self.assertIn("confirm the recipients and signer plan before anything is sent.", HTML)
        self.assertIn("const canRetryUnsent = agreement.status === 'failed' && !agreement.signwell_document_id;", HTML)
        self.assertIn("const canRetrySaved = agreement.canRetrySavedRequest === true && ['draft', 'failed'].includes(agreement.status);", HTML)
        self.assertIn("const canSend = signingEnabled && signingFormCodes.has(agreement.form_code) && ((!agreement.signwell_document_id && (agreement.status === 'draft' || canRetryUnsent)) || canRetrySaved);", HTML)
        self.assertIn("Retry signature request", HTML)

    def test_brokerage_profile_uses_finished_product_language(self):
        self.assertIn("<h4>Brokerage Profile</h4>", HTML)
        self.assertIn("Loading brokerage workspace...", HTML)
        self.assertIn("Save Brokerage Profile", HTML)
        self.assertIn("Brokerage profile saved.", HTML)
        self.assertNotIn("This account can now manage the brokerage workspace.", HTML)
        self.assertNotIn("Brokerage Branding Foundation", HTML)
        self.assertNotIn("foundation build.", HTML)
        self.assertNotIn("Submit Internal Note", HTML)

    def test_listing_workspace_avoids_internal_build_language(self):
        self.assertIn("Loading listing workspace...", HTML)
        self.assertIn("Seller and property details saved. You can create a listing workspace next.", HTML)
        self.assertIn("Add the property and seller first.", HTML)
        self.assertIn("Add the property and landlord first.", HTML)
        self.assertNotIn("Loading seller-side foundation...", HTML)
        self.assertNotIn("This proves the listing-tools path", HTML)
        self.assertNotIn("restricted-form authorization status", HTML)


class CustomerLanguagePolishTests(unittest.TestCase):
    def test_brokerage_summary_is_clear_without_programming_explanation(self):
        self.assertNotIn('not editable from the browser', HTML)
        self.assertIn('Membership: <strong>', HTML)
        self.assertIn('Loading team activity', HTML)

    def test_membership_copy_does_not_imply_forms_need_a_brokerage_seat(self):
        self.assertIn('You can still use your individual workspace, saved offers, and shared forms.', HTML)
        self.assertIn('Brokerage team features become available when your membership is active.', HTML)
        self.assertIn('Request brokerage activation', HTML)
        self.assertIn('No brokerage seat, team membership, broker action, or extra form-access step is required.', HTML)

    def test_privacy_and_team_label_limits_are_still_explicit(self):
        self.assertIn('Buyer names, property addresses, offer terms, and document contents are not included.', HTML)
        self.assertIn('Team labels are for your roster only.', HTML)
        self.assertIn('They do not change access, plans, offers, or documents.', HTML)

    def test_only_empty_plan_prompt_options_are_normalized(self):
        self.assertIn("option.value === ''", HTML)
        self.assertIn("option.textContent = 'Choose a payment plan…'", HTML)
        self.assertIn("closest('input, textarea, select, option, [contenteditable]')", HTML)
        self.assertIn("closest('button, input, textarea, select, option, [contenteditable]')", HTML)


if __name__ == "__main__":
    unittest.main()
