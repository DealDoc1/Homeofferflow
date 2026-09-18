from pathlib import Path
import json
import subprocess
import unittest


HTML = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")


class OfferWorkspaceSigningRecoveryTests(unittest.TestCase):
    def test_active_workspace_renders_retry_only_for_unsent_generated_offers(self):
        start = HTML.index('  function renderCard(o){')
        end = HTML.index('  function renderWorkspace(offers){', start)
        script = '''
const root = {}, cleanStatus = o => o.status, statusClass = () => '', money = String;
const subtitle = () => '', bucketForOffer = () => 'generated', needsAttention = () => false;
const addendaTags = () => [], esc = String, nextAction = () => '', dateShort = String;
const dateLong = String, signingLabel = () => '';
''' + HTML[start:end] + '''
const statuses = ['Generated', 'Generation Failed', 'Draft', 'Awaiting Signature', 'Expired'];
const results = statuses.map(status => renderCard({id:'test', status}).includes('>Retry signing</button>'));
results.push(renderCard({id:'test', status:'Generated', signwell_document_id:'existing'}).includes('>Retry signing</button>'));
results.push(renderCard({id:'test', status:'Generated', offer_data:{signwell:{response:{id:'existing'}}}}).includes('>Retry signing</button>'));
process.stdout.write(JSON.stringify(results));
'''
        result = subprocess.run(['node', '-e', script], capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(result.stdout), [True, True, False, False, False, False, False])

    def test_stale_buyer_signing_cards_offer_a_copy_only_follow_up_action(self):
        self.assertIn("const needsBuyerReminder = hasDoc && bucketForOffer(o) === 'signing' && needsAttention(o);", HTML)
        self.assertIn("Copy buyer reminder", HTML)
        self.assertIn("root.copyBuyerSigningReminder = async function(offerId)", HTML)
        self.assertIn("buyer_signing_reminder_copied", HTML)
        self.assertIn("const ageDays = Number.isFinite(updatedAt.getTime())", HTML)
        self.assertIn("has been awaiting completion for ${ageDays} day", HTML)

    def test_priority_follow_up_exposes_the_same_copy_only_reminder_without_a_second_navigation_step(self):
        self.assertIn("const priorityNeedsBuyerReminder = priority && bucketForOffer(priority) === 'signing';", HTML)
        self.assertIn("onclick=\"copyBuyerSigningReminder('${esc(priority.id)}')\"", HTML)

    def test_priority_signing_follow_up_can_refresh_status_before_an_agent_uses_a_reminder(self):
        self.assertIn("onclick=\"hofSyncPrioritySigningStatus(this)\">Sync SignWell now</button>", HTML)
        self.assertIn("root.hofSyncPrioritySigningStatus = async function(button)", HTML)
        self.assertIn("button.textContent = 'Syncing SignWell…'", HTML)
        self.assertIn("'priority_signing_sync_selected'", HTML)

    def test_reminder_requires_agent_review_before_any_external_communication(self):
        start = HTML.index("root.copyBuyerSigningReminder = async function(offerId)")
        end = HTML.index("root.hofRenderOfferWorkspaceV10", start)
        reminder = HTML[start:end]
        self.assertIn("Review it before sending through your approved communication channel.", reminder)
        self.assertNotIn("fetch('/api/", reminder)
        self.assertNotIn("mailto:", reminder)

    def test_created_provider_documents_do_not_prove_invitation_delivery(self):
        start = HTML.index("function bucketForOffer(o)")
        end = HTML.index("function signingLabel(o)", start)
        bucket = HTML[start:end]
        self.assertNotIn("if (status.includes('created') && hasDoc) return 'signing';", bucket)
        self.assertIn("if (status === 'draft - not sent') return 'generated';", bucket)

    def test_pending_signwell_documents_are_treated_as_in_progress(self):
        status = HTML[HTML.index("function getOfferBestStatus"):HTML.index("function getOfferSigningBucket")]
        self.assertIn("if (compact === 'pending') return 'Partially Signed';", status)
        self.assertIn("if (compact === 'pending') return 'Partially Signed';", HTML)
        api = (Path(__file__).resolve().parents[1] / "api" / "signwell-status.js").read_text(encoding="utf-8")
        self.assertIn("['signed', 'pending', 'in progress', 'partial', 'partially signed']", api)

    def test_automatic_signing_sync_includes_the_normalized_awaiting_buyer_status(self):
        start = HTML.index("root.hofRefreshOfferWorkspace = async function")
        end = HTML.index("root.hofReuseTermsFromMostRecentOffer", start)
        refresh = HTML[start:end]
        self.assertIn("'awaiting_buyer_signature'", refresh)
        self.assertIn("activeStatuses.has(status)", refresh)

    def test_current_provider_status_wins_over_historical_response_aliases(self):
        start = HTML.index("function getOfferBestStatus(offer = {})")
        end = HTML.index("function getOfferSigningBucket", start)
        status = HTML[start:end]
        self.assertIn("const signwellStatuses = [", status)
        self.assertIn("const completedStatus = signwellStatuses.find", status)
        self.assertIn("['buyer signatures complete', 'completed', 'complete', 'fully signed', 'buyer signed'].includes(normalized)", status)
        self.assertIn("const signwellStatus = offer.signwell_status || completedStatus || signwellStatuses[0] || '';", status)
        self.assertIn("const signwellStatus = getOfferBestStatus(offer);", HTML)

    def test_admin_dashboard_surfaces_only_an_aggregate_reminder_adoption_signal(self):
        backend = (Path(__file__).resolve().parents[1] / "api" / "admin-dashboard.py").read_text(encoding="utf-8")
        self.assertIn("buyer_signing_reminder_copied_count", backend)
        self.assertIn('"buyerSigningReminderCopiedCount"', backend)
        self.assertIn("buyerSigningReminderCopiedCount", HTML)
        self.assertIn("prioritySigningSyncSelectedCount", HTML)
        self.assertIn("priority SignWell syncs from stale signing workspaces", HTML)


if __name__ == "__main__":
    unittest.main()
