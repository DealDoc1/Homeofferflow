from copy import deepcopy
import json
import unittest

from lib.signwell_qa_readback import readback_report
from tests.test_signwell_controls import specimen


class SignwellQAReadbackTests(unittest.TestCase):
    def setUp(self):
        fields, groups, rules = specimen()
        fields[0][0].update(page=1, x=25, y=50, width=12, height=12)
        self.payload = {"id": "fixed-test", "name": "Fixed QA", "test_mode": True,
            "apply_signing_order": False, "metadata": {"revision": "fixed"},
            "fields": fields, "checkbox_groups": groups, "conditional_rules": rules,
            "recipients": [{"id": "1", "email": "qa@example.test", "name": "QA"}]}
        self.document = deepcopy(self.payload)

    def report(self):
        return readback_report(self.document, self.payload)

    def test_matching_readback_passes_without_mutation(self):
        before = deepcopy(self.document)
        self.assertTrue(all(self.report()["checks"].values()))
        self.assertEqual(self.document, before)

    def test_identifies_changed_geometry_and_text_constraint(self):
        self.document["fields"][0][0]["x"] = 30
        self.document["fields"][0][2]["fixed_width"] = False
        report = self.report()
        self.assertFalse(report["checks"]["geometry_and_recipients"])
        self.assertFalse(report["checks"]["completion_controls"])
        self.assertTrue(report["checks"]["checkbox_groups"])
        self.assertTrue(report["checks"]["conditional_rules"])
        self.assertIn({"field": "yes", "property": "x", "present": True,
            "expected": 25.0, "returned": 30.0}, report["differences"])

    def test_nullable_group_owner_and_group_owned_rule_are_observed_not_approved(self):
        self.document["checkbox_groups"][0].update(id="provider-group", recipient_id=None)
        self.document["conditional_rules"][0]["target_id"] = "provider-group"
        report = self.report()
        self.assertFalse(report["checks"]["checkbox_groups"])
        self.assertFalse(report["checks"]["conditional_rules"])
        self.assertFalse(report["checks"]["completion_controls"])
        self.assertTrue(next(d for d in report["differences"] if "group" in d)["recipient_is_null"])
        self.assertEqual(report["differences"][-1]["kind"], "group")

    def test_provider_strings_values_recipients_and_urls_are_never_returned(self):
        secret = "SECRET https://private.test/sign?token=hidden"
        self.document.update(name=secret, apply_signing_order=secret, metadata={"revision": secret}, private_key=secret)
        for field in self.document["fields"][0]:
            field.update(value=secret, validation_regex=secret, x=secret)
        self.document["recipients"][0].update(name=secret, email=secret)
        self.document["conditional_rules"][0]["target_id"] = secret
        self.document["checkbox_groups"][0].update(recipient_id=secret, exact_value=secret)
        result = json.dumps(self.report(), allow_nan=False)
        for value in ("SECRET", "private.test", "hidden", "qa@example.test", "provider-group"):
            self.assertNotIn(value, result)

    def test_nonfinite_and_malformed_readbacks_are_bounded(self):
        self.document["fields"][0][0]["x"] = float("nan")
        self.assertIn("non_scalar", json.dumps(self.report(), allow_nan=False))
        for value in (None, {}, [None], [[None]]):
            self.document["fields"] = value
            report = self.report()
            self.assertFalse(report["checks"]["geometry_and_recipients"])
            self.assertFalse(report["checks"]["readback_shape"])
            self.assertLess(len(json.dumps(report)), 2000)

    def test_duplicate_or_unrecognized_fields_fail_without_echoing_ids(self):
        self.document["fields"][0].append({"api_id": "SECRET_UNKNOWN", "id": "SECRET_ID"})
        report = self.report()
        self.assertFalse(report["checks"]["field_set"])
        self.assertNotIn("SECRET", json.dumps(report))


if __name__ == "__main__":
    unittest.main()
