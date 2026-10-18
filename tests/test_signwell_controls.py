from copy import deepcopy
import hashlib
import json
import unittest

from lib.signwell_controls import controls_match
from lib.signwell_delivery import request_fingerprint


def specimen():
    fields=[[{'api_id':'yes','type':'checkbox','recipient_id':'1','required':False},
             {'api_id':'no','type':'checkbox','recipient_id':'1','required':False},
             {'api_id':'details','type':'text','recipient_id':'1','required':False,'fixed_width':True,
              'validation':'custom','validation_regex':r'^[\s\S]{1,250}$','validation_regex_error_message':'Use 250 characters.'}]]
    groups=[{'group_name':'choice','recipient_id':'1','checkbox_ids':['yes','no'],'validation':'exact','required':True,'exact_value':1}]
    rules=[{'target_id':'yes','action_type':'require','action_field_ids':['details'],
            'conditions':[{'condition_type':'all_of','status':'completed','field_api_ids':['yes'],'position':1}]}]
    return fields,groups,rules


class SignwellControlTests(unittest.TestCase):
    def setUp(self):
        self.fields,self.groups,self.rules=specimen()
        self.document=deepcopy({'fields':self.fields,'checkbox_groups':self.groups,'conditional_rules':self.rules})

    def matches(self):return controls_match(self.document,self.fields,self.groups,self.rules)

    def test_exact_controls_pass_and_provider_ids_resolve_to_verified_api_ids(self):
        self.assertTrue(self.matches())
        for field in self.document['fields'][0]:field['id']='provider-'+field['api_id']
        self.document['checkbox_groups'][0]['checkbox_ids']=['provider-no','provider-yes']
        self.document['conditional_rules'][0]['id']='provider-rule-id'
        self.document['conditional_rules'][0]['conditions'][0]['join_operator']='or_operator'
        self.assertTrue(self.matches()) # First condition join has no semantics.

    def test_dropped_changed_or_unexpected_selection_constraints_fail(self):
        for key,value in (('required',False),('exact_value',2),('validation','minimum'),('recipient_id','2'),('checkbox_ids',['yes','missing'])):
            with self.subTest(key=key):
                old=deepcopy(self.document);self.document['checkbox_groups'][0][key]=value
                self.assertFalse(self.matches());self.document=old
        self.document.pop('checkbox_groups');self.assertFalse(self.matches())

    def test_conditional_requirement_cannot_disappear_or_watch_the_wrong_box(self):
        for key,value in (('action_type','show'),('target_id','no'),('action_field_ids',['yes'])):
            with self.subTest(key=key):
                old=deepcopy(self.document);self.document['conditional_rules'][0][key]=value
                self.assertFalse(self.matches());self.document=old
        self.document['conditional_rules'][0]['conditions'][0]['status']='not_completed'
        self.assertFalse(self.matches())

    def test_checkbox_required_and_text_length_controls_must_survive_readback(self):
        for field_index,key,value in ((0,'required',True),(2,'fixed_width',False),(2,'validation_regex','.*')):
            old=deepcopy(self.document);self.document['fields'][0][field_index][key]=value
            self.assertFalse(self.matches());self.document=old

    def test_control_changes_are_bound_but_legacy_fingerprint_is_byte_compatible(self):
        payload={'fields':self.fields,'recipients':[{'id':'1'}],'metadata':{'source':'QA'},'test_mode':True,'apply_signing_order':False,'embedded_signing':False}
        context={'source':'stable'}
        previous={'context':context,'metadata':payload['metadata'],'fields':self.fields,'recipients':payload['recipients'],
                  'test_mode':True,'apply_signing_order':False,'embedded_signing':False}
        expected=hashlib.sha256(json.dumps(previous,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
        self.assertEqual(request_fingerprint(payload,context),expected)
        self.assertEqual(request_fingerprint({**payload,'checkbox_groups':[],'conditional_rules':[]},context),expected)
        controlled={**payload,'checkbox_groups':self.groups,'conditional_rules':self.rules}
        first=request_fingerprint(controlled,context)
        self.assertNotEqual(first,expected)
        changed=deepcopy(controlled);changed['checkbox_groups'][0]['exact_value']=2
        self.assertNotEqual(first,request_fingerprint(changed,context))


if __name__=='__main__':unittest.main()
