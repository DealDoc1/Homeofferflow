import unittest
from unittest.mock import patch
from io import BytesIO
from pypdf import PdfReader
from lib import production_adapter as adapter
from test_controlled_launch import minimal_offer, configure_local_forms


class LeaseSelectionAuthorityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        configure_local_forms()

    def test_current_no_answer_overrides_a_legacy_fixture_yes(self):
        self.assertEqual(adapter.paragraph4_lease_kinds({
            'leases': 'yes', 'leaseResidential': 'yes',
            'leaseFixture': 'no', 'fixtureLease': 'yes',
        }), ['TXR-1953'])

    def test_current_no_answer_overrides_a_legacy_natural_resource_yes(self):
        self.assertFalse(adapter.natural_resource_lease_requested({
            'leases': 'yes', 'leaseNaturalResource': 'no', 'naturalResourceLease': 'yes',
        }))

    def test_no_leases_answer_ignores_all_stale_type_answers(self):
        offer = {'leases': 'no', 'leaseResidential': 'yes', 'fixtureLease': 'yes', 'naturalResourceLease': 'yes'}
        self.assertEqual(adapter.paragraph4_lease_kinds(offer), [])
        self.assertFalse(adapter.natural_resource_lease_requested(offer))
        self.assertEqual(adapter.paragraph4_execution_parties(offer), [])

    def test_legacy_only_positive_answers_remain_supported_when_parent_answer_is_absent(self):
        self.assertEqual(adapter.paragraph4_lease_kinds({'fixtureLease': 'yes'}), ['TXR-1954'])
        self.assertTrue(adapter.natural_resource_lease_requested({'naturalResourceLease': 'yes'}))

    def test_legacy_type_labels_remain_supported(self):
        self.assertEqual(adapter.paragraph4_lease_kinds({'leases': 'residential lease'}), ['TXR-1953'])
        self.assertEqual(adapter.paragraph4_lease_kinds({'leases': 'fixtureLease'}), ['TXR-1954'])
        self.assertTrue(adapter.natural_resource_lease_requested({'leases': 'naturalResourceLease'}))

    def test_current_no_type_answer_also_overrides_an_old_type_label(self):
        self.assertEqual(adapter.paragraph4_lease_kinds({'leases': 'fixture', 'leaseFixture': 'no'}), [])
        self.assertFalse(adapter.natural_resource_lease_requested({'leases': 'naturalresource', 'leaseNaturalResource': 'no'}))

    def test_render_normalization_does_not_rewrite_saved_answers(self):
        offer = {'leases': 'no', 'fixtureLease': 'yes', 'naturalResourceLease': 'yes'}
        before = dict(offer)
        normalized = adapter._paragraph4_verified_offer(offer)
        self.assertEqual(offer, before)
        self.assertEqual(normalized['fixtureLease'], 'no')
        self.assertEqual(normalized['naturalResourceLease'], 'no')

    def test_current_yes_choices_survive_old_no_aliases(self):
        offer = {'leases': 'yes', 'leaseResidential': 'yes', 'leaseFixture': 'yes', 'fixtureLease': 'no',
                 'leaseNaturalResource': 'yes', 'naturalResourceLease': 'no'}
        self.assertEqual(adapter.paragraph4_lease_kinds(offer), ['TXR-1953', 'TXR-1954'])
        self.assertTrue(adapter.natural_resource_lease_requested(offer))
        normalized = adapter._paragraph4_verified_offer(offer)
        self.assertEqual(normalized['fixtureLease'], 'yes')
        self.assertEqual(normalized['naturalResourceLease'], 'yes')

    def test_blank_current_answers_keep_legacy_compatibility(self):
        offer = {'leaseFixture': '', 'fixtureLease': 'yes', 'leaseNaturalResource': None, 'naturalResourceLease': 'yes'}
        self.assertEqual(adapter.paragraph4_lease_kinds(offer), ['TXR-1954'])
        self.assertTrue(adapter.natural_resource_lease_requested(offer))

    def test_no_leases_packet_ignores_stale_details_and_preserves_purchase_geometry(self):
        base = minimal_offer()
        stale = minimal_offer(leaseResidential='yes', fixtureLease='yes', naturalResourceLease='yes',
                              paragraph4Seller1Name='Old hidden signer', paragraph4Seller1Email='old@example.com')
        adapter.validate_supported_offer(stale)
        with patch.object(adapter.verified, 'build_pages_data', wraps=adapter.verified.build_pages_data) as pages:
            packet = adapter.fill_and_merge_20_19(stale)
        self.assertEqual(len(PdfReader(BytesIO(packet)).pages), 12)
        printed = pages.call_args.args[0]
        self.assertEqual(printed['leaseResidential'], 'no')
        self.assertEqual(printed['fixtureLease'], 'no')
        self.assertEqual(printed['naturalResourceLease'], 'no')
        base_packet = adapter.fill_and_merge_20_19(base)
        self.assertEqual(adapter.build_signwell_fields_20_19(stale, packet),
                         adapter.build_signwell_fields_20_19(base, base_packet))

    def test_natural_resource_packet_omits_a_deselected_legacy_fixture_addendum(self):
        offer = minimal_offer(leases='yes', leaseFixture='no', fixtureLease='yes',
                              leaseNaturalResource='yes', leaseNRDelivered='no', naturalResourceTerminationDays='7')
        adapter.validate_supported_offer(offer)
        packet = adapter.fill_and_merge_20_19(offer)
        self.assertEqual(len(PdfReader(BytesIO(packet)).pages), 12)
        self.assertEqual(adapter.paragraph4_execution_parties(offer), [])
        self.assertNotIn('TXR-1954', offer['_signing_render_revisions'])
