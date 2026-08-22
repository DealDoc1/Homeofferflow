from pathlib import Path
import re
import unittest


INDEX_PATH = Path(__file__).resolve().parents[1] / "index.html"
HTML = INDEX_PATH.read_text(encoding="utf-8")


class AgentActivationDashboardTests(unittest.TestCase):
    def test_platform_admin_exposes_aggregate_agent_activation_metrics_only(self):
        api = (INDEX_PATH.parent / "api" / "admin-dashboard.py").read_text(encoding="utf-8")

        for expected in (
            "agentProfileCompleteCount",
            "agentFirstOfferCount",
            "agentRepeatOfferCount",
            "agentUpdatedDraftCount",
        ):
            self.assertIn(expected, api)

        self.assertIn(
            "hof_offers?role=eq.agent&deleted_at=is.null&select=user_id,status,signwell_status,created_at,updated_at",
            api,
        )
        self.assertNotIn("buyer_name", api[api.index("agent_lifecycle_offers"):api.index("events =")])

    def test_platform_admin_renders_agent_activation_funnel_metrics(self):
        for expected in (
            "Agent Profiles Ready",
            "Agents With a Saved Offer",
            "Repeat-Offer Agents",
            "Updated Agent Drafts",
        ):
            self.assertIn(expected, HTML)

    def test_activation_card_is_present_in_dashboard(self):
        dashboard_start = HTML.index('id="accountPanelDashboard"')
        dashboard_end = HTML.index('id="accountPanelProfile"')
        dashboard = HTML[dashboard_start:dashboard_end]

        self.assertIn('id="agentActivationCard"', dashboard)
        self.assertLess(
            dashboard.index('id="agentActivationCard"'),
            dashboard.index('id="betaOnboardingChecklist"'),
        )

    def test_activation_card_suppresses_only_the_redundant_dashboard_actions(self):
        self.assertIn('dashboard-legacy-actions', HTML)
        self.assertIn(
            '.agent-activation-card.show ~ .account-actions-row.dashboard-legacy-actions { display: none; }',
            HTML,
        )

    def test_dashboard_waits_for_offers_before_rendering_activation_state(self):
        function_match = re.search(
            r"async function openAccountDashboard\(opts = \{\}\) \{(?P<body>.*?)\n  \}",
            HTML,
            re.DOTALL,
        )
        self.assertIsNotNone(function_match)
        body = function_match.group("body")

        self.assertIn("await loadMyOffers();", body)
        self.assertLess(body.index("await loadMyOffers();"), body.index("renderAccountDashboard();"))

    def test_new_agent_post_login_routes_to_the_activation_dashboard_first(self):
        function_match = re.search(
            r"async function openAccountDashboard\(opts = \{\}\) \{(?P<body>.*?)\n  \}",
            HTML,
            re.DOTALL,
        )
        self.assertIsNotNone(function_match)
        body = function_match.group("body")
        self.assertIn("showAccountTab(opts.tab || 'dashboard');", body)
        self.assertNotIn("opts.postLogin && !isProfileMeaningful() ? 'profile'", body)

    def test_offer_loader_persists_offer_state_for_activation_card(self):
        self.assertIn("hofAuth.myOffers = loadedOffers;", HTML)
        self.assertIn("renderAgentActivationCard();", HTML)

    def test_activation_funnel_has_profile_offer_and_subscription_steps(self):
        script_start = HTML.index('id="hof-agent-activation-v16-js"')
        script_end = HTML.index("</script>", script_start)
        script = HTML[script_start:script_end]

        for expected in (
            "Profile and defaults",
            "First saved offer",
            "Active subscription",
            "Agent Activation Dashboard Viewed",
            "Agent Activation Action",
        ):
            self.assertIn(expected, script)

    def test_first_offer_starts_with_transaction_choice_before_profile_defaults(self):
        script_start = HTML.index('id="hof-agent-activation-v16-js"')
        script_end = HTML.index("</script>", script_start)
        script = HTML[script_start:script_end]

        first_offer = script.index("if (!hasOffer) {")
        profile_after_offer = script.index("if (!hasProfile) {", first_offer + 1)
        self.assertLess(first_offer, profile_after_offer)
        self.assertIn("Choose the transaction in front of you", script)
        self.assertIn("Choose Transaction", script)
        self.assertIn("Choose buying, sale listing, lease listing, or lease representation", script)
        self.assertIn("Set Up My Defaults", script)

    def test_first_offer_state_explains_the_transaction_choice_and_safe_draft_boundary(self):
        script_start = HTML.index('id="hof-agent-activation-v16-js"')
        script_end = HTML.index("</script>", script_start)
        script = HTML[script_start:script_end]

        self.assertIn("confidence: true", script)
        self.assertIn("First offer workflow overview", script)
        self.assertIn("Choose the transaction first.", script)
        self.assertIn("Saving a draft does not send a packet or request a signature.", script)

    def test_onboarding_uses_a_real_saved_draft_path_not_demo_only_language(self):
        self.assertIn("Start your first saved offer", HTML)
        self.assertIn("Start First Saved Offer", HTML)
        self.assertIn("Saving a draft does not generate a packet or request a signature.", HTML)

    def test_account_dashboard_resumes_same_role_local_drafts_before_clearing_them(self):
        self.assertIn("if (resumeLocalAccountOfferDraft(role)) return;", HTML)
        self.assertIn("function resumableAccountOfferDraft(role)", HTML)
        self.assertIn("String(draft.userType || '').toLowerCase() === normalizedRole", HTML)
        self.assertIn("surface: 'account_dashboard'", HTML)
        self.assertIn("agent_local_draft_resumed", HTML)
        self.assertIn("userType: typeof state !== 'undefined' ? state.data?.userType || 'homebuyer' : 'homebuyer'", HTML)

    def test_activation_card_offers_saved_draft_resume_or_explicit_fresh_start(self):
        script_start = HTML.index('id="hof-agent-activation-v16-js"')
        script_end = HTML.index("</script>", script_start)
        script = HTML[script_start:script_end]
        self.assertIn("key: 'resume_local_draft'", script)
        self.assertIn("Resume Saved Offer", script)
        self.assertIn("Start Fresh Offer", script)
        self.assertIn("action === 'resume_local'", script)
        self.assertIn("action === 'start_fresh'", script)

    def test_profile_activation_requires_agent_contact_and_license_fields(self):
        script_start = HTML.index('id="hof-agent-activation-v16-js"')
        script_end = HTML.index("</script>", script_start)
        script = HTML[script_start:script_end]

        for field in (
            "profile.agent_name",
            "profile.license_number",
            "profile.agent_email",
            "profile.agent_phone",
            "profile.brokerage_name",
        ):
            self.assertIn(field, script)

    def test_profile_form_makes_the_five_activation_essentials_clear_before_optional_defaults(self):
        profile_start = HTML.index('function renderAccountProfileForm()')
        profile_end = HTML.index('function escapeAttr(', profile_start)
        profile = HTML[profile_start:profile_end]

        self.assertIn('Save these five essentials first.', profile)
        self.assertIn('Title, escrow, and offer preferences below are optional', profile)
        self.assertEqual(profile.count('account-profile-required'), 5)
        for field in ('profAgentName', 'profAgentLicense', 'profAgentEmail', 'profAgentPhone', 'profBrokerageName'):
            self.assertIn(field, profile)

    def test_profile_save_explains_and_focuses_missing_repeat_offer_essentials(self):
        start = HTML.index("async function saveAccountProfile()")
        end = HTML.index("function setInputIfEmpty", start)
        profile_save = HTML[start:end]
        self.assertIn("const requiredProfileFields = [", profile_save)
        self.assertIn("const missingProfileFields", profile_save)
        self.assertIn("Add ' + missingProfileFields.join(', ') + ' to save your repeat-offer defaults.", profile_save)
        self.assertIn("?.focus();", profile_save)

    def test_profile_activation_names_the_five_defaults_before_opening_the_form(self):
        script_start = HTML.index('id="hof-agent-activation-v16-js"')
        script_end = HTML.index("</script>", script_start)
        script = HTML[script_start:script_end]
        self.assertIn("Finish your five repeat-offer defaults", script)
        self.assertIn("name, license number, business email, phone, and brokerage", script)
        self.assertIn("title, escrow, and common terms can be added later", script)

    def test_saved_client_draft_stays_resumable_before_optional_repeat_offer_defaults(self):
        script_start = HTML.index('id="hof-agent-activation-v16-js"')
        script_end = HTML.index("</script>", script_start)
        script = HTML[script_start:script_end]
        profile_start = script.index("if (!hasProfile) {")
        profile_end = script.index("if (billingRecoveryNeeded)", profile_start)
        profile = script[profile_start:profile_end]
        self.assertIn("if (draft)", profile)
        self.assertIn("key: 'profile_with_draft'", profile)
        self.assertIn("primary: 'Resume My Draft'", profile)
        self.assertIn("secondary: 'Save My Defaults'", profile)
        self.assertIn("state.key === 'profile_with_draft' ? 'resume'", script)
        self.assertIn("state.key === 'profile_with_draft' ? 'profile'", script)

    def test_profile_completion_signal_matches_activation_requirements(self):
        readiness_start = HTML.index('id="hof-agent-activation-v16-js"')
        readiness_end = HTML.index("</script>", readiness_start)
        readiness = HTML[readiness_start:readiness_end]
        self.assertIn("root.isProfileReadyForDefaults = profileComplete;", readiness)
        self.assertIn("profile = profile || {};", readiness)

        broker_start = HTML.index('id="hof-broker-role-v14-js"')
        broker_end = HTML.index("</script>", broker_start)
        broker = HTML[broker_start:broker_end]
        self.assertIn("root.isProfileReadyForDefaults(profile)", broker)
        self.assertIn("it is not a", broker)

    def test_activation_actions_cover_primary_account_paths(self):
        script_start = HTML.index('id="hof-agent-activation-v16-js"')
        script_end = HTML.index("</script>", script_start)
        script = HTML[script_start:script_end]

        for action in ("profile", "new_offer", "choose_transaction", "offers", "resume", "subscribe", "reuse_terms", "billing"):
            self.assertRegex(script, rf"action === ['\"]{action}['\"]")

    def test_first_offer_activation_action_reveals_the_four_transaction_choices_without_creating_a_draft(self):
        self.assertIn("window.openAgentTransactionPicker = function openAgentTransactionPicker()", HTML)
        self.assertIn("picker.scrollIntoView({ behavior: 'smooth', block: 'center' });", HTML)
        self.assertIn("picker.focus({ preventScroll: true });", HTML)
        self.assertIn("Choose the transaction you are working on to continue.", HTML)
        self.assertIn('id="agentWorkflowStart" style="margin-top:1rem;" tabindex="-1"', HTML)
        self.assertIn('Question 1', HTML)
        self.assertIn('What kind of transaction are you starting?', HTML)
        for label in ('>Buying</button>', '>Listing</button>', '>Lease listing</button>', '>Lease representation</button>'):
            self.assertIn(label, HTML)

    def test_activation_actions_record_stage_and_primary_or_secondary_choice(self):
        script_start = HTML.index('id="hof-agent-activation-v16-js"')
        script_end = HTML.index("</script>", script_start)
        script = HTML[script_start:script_end]

        self.assertIn("activationKey", script)
        self.assertIn("control === 'primary' || control === 'secondary'", script)
        self.assertIn("'primary','${safe(state.key)}'", script)
        self.assertIn("'secondary','${safe(state.key)}'", script)

    def test_subscription_activation_offers_monthly_and_annual_checkout_choices(self):
        script_start = HTML.index('id="hof-agent-activation-v16-js"')
        script_end = HTML.index("</script>", script_start)
        script = HTML[script_start:script_end]

        self.assertIn("primary: 'Choose Monthly'", script)
        self.assertIn("secondary: 'Choose Annual'", script)
        self.assertIn("billing === 'annual' ? 'annual' : 'monthly'", script)
        self.assertIn("activationKey === 'reactivate' ? 'subscription_reactivation' : 'agent_activation'", script)
        self.assertIn("startSubscriptionCheckout?.(plan, normalizedBilling, source)", script)

    def test_beta_agent_with_a_saved_draft_resumes_client_work_before_checkout(self):
        script_start = HTML.index('id="hof-agent-activation-v16-js"')
        script_end = HTML.index("</script>", script_start)
        script = HTML[script_start:script_end]

        beta_resume = script.index("if (subscriptionStatus === 'beta' && draft)")
        generic_subscription = script.index("if (!hasPlan)", beta_resume + 1)
        self.assertLess(beta_resume, generic_subscription)
        self.assertIn("key: 'resume_beta'", script)
        self.assertIn("primary: 'Resume Offer'", script)
        self.assertIn("secondary: 'Explore Monthly Access'", script)
        self.assertIn("state.key === 'resume_beta' ? 'resume'", script)
        self.assertIn("state.key === 'resume_beta' ? 'subscribe'", script)
        self.assertIn("Your beta workspace is active", script)

    def test_canceled_accounts_use_reactivation_attribution(self):
        script_start = HTML.index('id="hof-agent-activation-v16-js"')
        script_end = HTML.index("</script>", script_start)
        script = HTML[script_start:script_end]

        self.assertIn("function subscriptionRecoveryNeeded()", script)
        self.assertIn("function subscriptionReplacementCheckoutNeeded()", script)
        self.assertIn("key: 'reactivate'", script)
        self.assertIn("primary: 'Restore Monthly'", script)
        self.assertIn("secondary: 'Restore Annual'", script)
        self.assertIn("activationKey === 'reactivate' ? 'subscription_reactivation' : 'agent_activation'", script)

    def test_payment_attention_accounts_use_billing_recovery_not_new_checkout(self):
        script_start = HTML.index('id="hof-agent-activation-v16-js"')
        script_end = HTML.index("</script>", script_start)
        script = HTML[script_start:script_end]

        self.assertIn("function subscriptionBillingRecoveryNeeded()", script)
        self.assertIn("return ['past_due', 'incomplete', 'unpaid', 'paused'].includes(status);", script)
        self.assertIn("return ['canceled', 'incomplete_expired'].includes(status);", script)
        self.assertIn("key: 'recover_billing'", script)
        self.assertIn("primary: 'Fix Billing'", script)
        self.assertIn("action === 'billing'", script)
        self.assertIn("openBillingPortal?.('activation_billing_recovery')", script)
        self.assertIn("state.key === 'recover_billing' ? 'billing'", script)

    def test_active_subscription_keeps_next_offer_action_visible(self):
        subscription_start = HTML.index("function renderSubscriptionCard()")
        subscription_end = HTML.index("async function openBillingPortal", subscription_start)
        subscription = HTML[subscription_start:subscription_end]

        self.assertIn("const remaining = Math.max(0, limit - used);", subscription)
        self.assertIn('Create Next Offer', subscription)
        self.assertIn("remaining + ' packet'", subscription)
        self.assertIn("startAccountOffer()", subscription)

    def test_repeat_activation_reuses_terms_without_reusing_client_or_property(self):
        script_start = HTML.index('id="hof-agent-activation-v16-js"')
        script_end = HTML.index("</script>", script_start)
        script = HTML[script_start:script_end]

        self.assertIn("function mostRecentOffer()", script)
        self.assertIn("primary: 'Reuse Last Terms'", script)
        self.assertIn("secondary: 'Create Fresh Offer'", script)
        self.assertIn("state.key === 'repeat' ? 'reuse_terms'", script)
        self.assertIn("root.reuseOfferTerms?.(offerId)", script)

    def test_resume_activation_chooses_the_most_recent_draft(self):
        script_start = HTML.index('id="hof-agent-activation-v16-js"')
        script_end = HTML.index("</script>", script_start)
        script = HTML[script_start:script_end]
        draft_start = script.index("function draftOffer()")
        draft_end = script.index("function mostRecentOffer()", draft_start)
        draft = script[draft_start:draft_end]
        self.assertIn("offers().filter", draft)
        self.assertIn("return bUpdated - aUpdated", draft)

    def test_returning_agent_can_start_a_clean_offer_without_detouring_to_the_workspace(self):
        script_start = HTML.index('id="hof-agent-activation-v16-js"')
        script_end = HTML.index("</script>", script_start)
        script = HTML[script_start:script_end]
        self.assertIn("primary: 'Resume My Draft'", script)
        self.assertIn("secondary: 'Create Fresh Offer'", script)
        self.assertIn("state.key === 'resume' ? 'start_fresh'", script)
        self.assertIn("start a clean offer for a different client", script)

    def test_legacy_demo_card_is_removed_by_final_dashboard_renderer(self):
        script_start = HTML.index('id="hof-agent-activation-v16-js"')
        script_end = HTML.index("</script>", script_start)
        script = HTML[script_start:script_end]

        self.assertIn("release15DashboardCard", script)
        self.assertIn("?.remove()", script)


if __name__ == "__main__":
    unittest.main()
