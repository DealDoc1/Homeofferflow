import json
from pathlib import Path
import subprocess
import unittest


HTML = (Path(__file__).resolve().parents[1] / 'index.html').read_text()


class PacketDeliverySummaryTests(unittest.TestCase):
    def summary(self, options):
        start = HTML.index('  function packetDeliverySummary(')
        end = HTML.index('  function showPaymentSuccess(', start)
        script = HTML[start:end] + '\nprocess.stdout.write(JSON.stringify(packetDeliverySummary(' + \
            json.dumps('agent@example.com') + ', ' + json.dumps(options) + ', ' + \
            json.dumps({'buyerEmail': 'buyer@example.com'}) + ')));'
        result = subprocess.run(['node', '-e', script], text=True, capture_output=True, check=True)
        return json.loads(result.stdout)

    def test_agent_sees_buyer_destination_and_independent_signing(self):
        result = self.summary({'packetGenerated': True, 'documentEmail': {'status': 'accepted'}, 'signwell': {'ok': True}})
        self.assertEqual(result['recipient'], 'buyer@example.com')
        self.assertIn('buyer@example.com', result['message'])
        self.assertIn('Each signer can sign independently', result['signing'])

    def test_failed_missing_or_disabled_signing_does_not_claim_invitation_sent(self):
        for signing in ({'ok': False, 'enabled': True}, None, {'enabled': False}):
            with self.subTest(signing=signing):
                result = self.summary({'packetGenerated': True, 'signwell': signing})
                self.assertNotIn('has sent', result['signing'])
                self.assertIn('email delivery is not confirmed', result['message'])
                if signing != {'enabled': False}:
                    self.assertIn('Retry signing', result['signing'])

    def test_unconfirmed_checkout_does_not_claim_email_or_signatures_sent(self):
        result = self.summary({'checkoutConfirmationPending': True})
        self.assertEqual(result['label'], 'Delivery email')
        self.assertIn('after payment is confirmed', result['message'])
        self.assertNotIn('has sent', result['signing'])

    def test_provider_acceptance_does_not_claim_inbox_delivery(self):
        result = self.summary({'packetGenerated': True, 'documentEmail': {'status': 'accepted'}})
        self.assertIn('has been requested', result['message'])
        self.assertNotIn('were emailed', result['message'])
        self.assertIn('including spam', result['delivery'])

    def test_uncertain_signing_does_not_offer_another_invitation(self):
        result = self.summary({'packetGenerated': True, 'signwell': {'ok': False, 'deliveryUnconfirmed': True}})
        self.assertIn('Signing delivery is not confirmed', result['signing'])
        self.assertNotIn('Retry signing', result['signing'])

    def render_success(self, options, data=None, click_primary=False, subscription_generated=True):
        start = HTML.index('  function packetDeliverySummary(')
        end = HTML.index('  function backToHomeAfterPayment(', start)
        harness = '''
          const elements = Object.fromEntries(['successEmail', 'successEmailLabel',
            'successMessage', 'successHeading', 'successDeliveryStep',
            'successSignatureStep', 'successRevisionStep', 'successPrimaryAction'].map(id => [id, {textContent:''}]));
          const document = {getElementById: id => elements[id] || null};
          const window = {__hofSubscriptionPacketGenerated:true, setTimeout:()=>{}};
          const removed = [];
          const localStorage = {removeItem:key=>removed.push(key)};
          const sessionStorage = {removeItem:key=>removed.push(key)};
          const HOF_STORAGE_KEY = 'draft';
          const trackEvent = () => {};
          const getCurrentSteps = () => ['stepSuccess'];
          let displayed = -1;
          const showStep = index => displayed = index;
          const renderNowWhatPartnerJourney = () => {};
          const navigation = [];
          const sideEffects = {saves:[], logs:[], usage:[]};
          const saveOfferDraftToSupabase = status => {sideEffects.saves.push(status);return Promise.resolve({id:'saved-offer'});};
          const logOfferEvent = (...args) => sideEffects.logs.push(args);
          const recordUsageEvent = (...args) => sideEffects.usage.push(args);
          const backToHomeAfterPayment = () => navigation.push('close-wizard');
          const openAccountDashboard = options => navigation.push(options.tab);
        '''
        state = {'buyerEmail': 'buyer@example.com', 'userType': 'agent', **(data or {})}
        script = harness + '\nconst state = ' + json.dumps({'data': state}) + ';\n' + HTML[start:end]
        script += '\nwindow.__hofSubscriptionPacketGenerated = ' + json.dumps(subscription_generated) + ';'
        script += '\nshowPaymentSuccess("agent@example.com", ' + json.dumps(options) + ');'
        if click_primary:
            script += '\nelements.successPrimaryAction.onclick();'
        script += '\nPromise.resolve().then(()=>process.stdout.write(JSON.stringify({elements,removed,displayed,navigation,sideEffects})));'
        result = subprocess.run(['node', '-e', script], text=True, capture_output=True, check=True)
        return json.loads(result.stdout)

    def test_success_screen_uses_actual_recipient_and_failed_send_next_step(self):
        rendered = self.render_success({'packetGenerated': True, 'signwell': {'ok': False}})
        fields = rendered['elements']
        self.assertEqual(fields['successEmail']['textContent'], 'buyer@example.com')
        self.assertEqual(fields['successHeading']['textContent'], 'Packet generated')
        self.assertIn('Retry signing', fields['successSignatureStep']['textContent'])
        self.assertEqual(rendered['displayed'], 0)

    def test_pending_checkout_preserves_draft_and_never_claims_generated(self):
        rendered = self.render_success({'checkoutConfirmationPending': True})
        self.assertEqual(rendered['removed'], [])
        self.assertEqual(rendered['elements']['successHeading']['textContent'], 'We’re confirming your checkout')
        self.assertEqual(rendered['elements']['successEmailLabel']['textContent'], 'Delivery email')

    def test_displaying_checkout_result_never_writes_offer_status_or_usage(self):
        for role in ('homebuyer', 'agent', 'investor', 'brokerage_admin'):
            for options in ({'checkoutConfirmationPending': True}, {},
                            {'packetGenerated': True, 'documentEmail': {'status': 'accepted'}}):
                with self.subTest(role=role, options=options):
                    rendered = self.render_success(options, {'userType': role}, subscription_generated=False)
                    self.assertEqual(rendered['sideEffects'], {'saves': [], 'logs': [], 'usage': []})

    def test_pending_email_preserves_draft_and_keeps_confirmed_signing_visible(self):
        rendered = self.render_success({'packetGenerated': True, 'documentEmail': {'status': 'unconfirmed'},
                                        'signwell': {'ok': True}})
        self.assertEqual(rendered['removed'], [])
        fields = rendered['elements']
        self.assertIn('do not need to generate another packet', fields['successMessage']['textContent'])
        self.assertIn('My Offers', fields['successDeliveryStep']['textContent'])
        self.assertEqual(fields['successPrimaryAction']['textContent'], 'View My Offers')
        self.assertIn('has sent', fields['successSignatureStep']['textContent'])

    def test_confirmed_email_clears_draft(self):
        rendered = self.render_success({'packetGenerated': True, 'documentEmail': {'status': 'accepted'}})
        self.assertEqual(rendered['removed'], ['draft', 'hofOfferData'])

    def test_primary_action_opens_existing_offers_tab_only_for_account_workflows(self):
        result = self.render_success({'packetGenerated': True}, click_primary=True)
        self.assertEqual(result['navigation'], ['close-wizard', 'offers'])
        result = self.render_success({'checkoutConfirmationPending': True}, {'userType': 'homebuyer'}, click_primary=True)
        self.assertEqual(result['navigation'], ['close-wizard'])
        self.assertEqual(result['elements']['successPrimaryAction']['textContent'], 'Back to Home')

    def test_lease_success_keeps_roles_but_invites_signers_together(self):
        rendered = self.render_success({'packetGenerated': True, 'signwell': {'ok': True}}, {'leaseResidential': 'yes'})
        signing = rendered['elements']['successSignatureStep']['textContent']
        self.assertIn('invitations together', signing)
        self.assertIn('Sellers sign the included Residential Lease Addendum', signing)
