import asyncio
import copy
import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest.mock import AsyncMock, patch
from urllib.parse import parse_qs, urlparse

import httpx

SPEC = importlib.util.spec_from_file_location('invite_retry_admin', Path(__file__).resolve().parents[1] / 'api/admin-dashboard.py')
admin = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(admin)
REAL_CLIENT = httpx.AsyncClient
ACTOR = {'id': '33333333-3333-3333-3333-333333333333', 'email': 'agent@example.test'}
BROKERAGE = '22222222-2222-2222-2222-222222222222'
TOKEN = 'a' * 32


class Store:
    def __init__(self):
        self.invite = {'id': 'invite-1', 'invite_token': TOKEN, 'brokerage_id': BROKERAGE,
                       'email': ACTOR['email'], 'role': 'agent', 'status': 'pending',
                       'expires_at': '2035-01-01T00:00:00Z', 'accepted_by': None}
        self.profile = None
        self.member = None
        self.brokerage = {'id': BROKERAGE, 'is_active': True, 'user_cap': 10}
        self.writes, self.reads = [], []
        self.fail_once = None
        self.empty_once = None

    def accepted(self):
        self.invite.update(status='accepted', accepted_by=ACTOR['id'])
        self.profile = {**ACTOR, 'role': 'agent', 'brokerage_id': BROKERAGE}
        self.member = {'id': 'member-1', 'user_id': ACTOR['id'], 'brokerage_id': BROKERAGE,
                       'role': 'agent', 'status': 'active'}
        return self

    async def get(self, route):
        self.reads.append(route)
        url = urlparse('https://fixture.invalid/' + route)
        row = {'hof_brokerage_invites': self.invite, 'hof_profiles': self.profile,
               'hof_brokerage_members': self.member, 'hof_brokerages': self.brokerage}[url.path.lstrip('/')]
        if row is None:
            return []
        for key, values in parse_qs(url.query).items():
            if key in {'select', 'limit'}:
                continue
            expr = values[0]
            value = str(row.get(key, '')).lower() if isinstance(row.get(key), bool) else str(row.get(key, ''))
            if expr.startswith('eq.') and value != expr[3:]:
                return []
            if expr.startswith('in.(') and value not in expr[4:-1].split(','):
                return []
        return [copy.deepcopy(row)]

    def handle(self, request):
        assert request.url.host == 'fixture.invalid', 'No external calls allowed'
        table = request.url.path.rsplit('/', 1)[1]
        field = {'hof_profiles': 'profile', 'hof_brokerage_members': 'member', 'hof_brokerage_invites': 'invite'}[table]
        payload = json.loads(request.content)
        self.writes.append((request.method, table, copy.deepcopy(payload)))
        if self.empty_once == field:
            self.empty_once = None
            return httpx.Response(200, json=[])
        if self.fail_once == field:
            self.fail_once = None
            return httpx.Response(503, json={'error': 'fictional transient failure'})
        row = getattr(self, field)
        if request.method == 'POST':
            if row is not None:
                return httpx.Response(409, json=[])
            row = {'id': payload.get('id', field + '-1')}
            setattr(self, field, row)
        row.update(payload)
        if self.fail_once == 'invite_after' and field == 'invite':
            self.fail_once = None
            raise httpx.ReadTimeout('Fictional final response lost', request=request)
        return httpx.Response(201 if request.method == 'POST' else 200, json=[copy.deepcopy(row)])


class BrokerageInviteRetryTests(unittest.TestCase):
    def call(self, store, actor=None, handler=False):
        actor = actor or ACTOR
        def client(*args, **kwargs):
            return REAL_CLIENT(*args, **kwargs, transport=httpx.MockTransport(store.handle))
        with patch.object(admin, 'SUPABASE_URL', 'https://fixture.invalid'), \
             patch.object(admin, 'SUPABASE_SERVICE_ROLE_KEY', 'fixture-only'), \
             patch.object(admin, '_get', side_effect=store.get), \
             patch.object(admin, '_require_available_agent_seat', AsyncMock()), \
             patch.object(admin.httpx, 'AsyncClient', side_effect=client):
            if not handler:
                return asyncio.run(admin._accept_brokerage_invite(actor, {'invite_token': TOKEN}))
            request = object.__new__(admin.handler)
            body = json.dumps({'action': 'accept_brokerage_invite', 'invite_token': TOKEN}).encode()
            request.path = '/api/admin-dashboard'
            request.headers = {'authorization': 'Bearer fictional-session', 'Content-Length': str(len(body))}
            request.rfile = io.BytesIO(body)
            with patch.object(admin, '_verified_user', AsyncMock(return_value=actor)), patch.object(admin, '_json') as response:
                request.do_POST()
            return response.call_args.args[1:]

    def test_lost_final_response_retries_as_read_only_success(self):
        s = Store(); s.fail_once = 'invite_after'
        with self.assertRaises(httpx.ReadTimeout):
            self.call(s)
        self.assertEqual(s.invite['status'], 'accepted')
        before = copy.deepcopy((s.invite, s.profile, s.member, s.writes))
        self.assertEqual(self.call(s), {'brokerageId': BROKERAGE, 'accepted': True})
        self.assertEqual((s.invite, s.profile, s.member, s.writes), before)

    def test_partial_membership_failure_keeps_invite_retryable_without_duplicates(self):
        s = Store(); s.fail_once = 'member'
        with self.assertRaises(RuntimeError): self.call(s)
        self.assertEqual(s.invite['status'], 'pending')
        self.assertIsNone(s.member)
        self.assertTrue(self.call(s)['accepted'])
        self.assertEqual(sum(method == 'POST' and table == 'hof_profiles' for method, table, _ in s.writes), 1)
        self.assertEqual(s.member['user_id'], ACTOR['id'])

    def test_accepted_retry_never_restores_suspended_or_removed_access(self):
        for status in ('suspended', 'removed', 'pending'):
            s = Store().accepted(); s.member['status'] = status
            with self.subTest(status=status), self.assertRaises((PermissionError, ValueError)):
                self.call(s)
            self.assertEqual(s.writes, [])

    def test_accepted_retry_requires_original_actor_and_email(self):
        for change in ('actor', 'email'):
            s = Store().accepted()
            if change == 'actor': s.invite['accepted_by'] = 'another-user'
            else: s.invite['email'] = 'other@example.test'
            with self.subTest(change=change), self.assertRaises(PermissionError): self.call(s)
            self.assertEqual(s.writes, [])

    def test_retry_does_not_grant_broker_privileges_or_switch_brokerage(self):
        for change in ('profile_role', 'admin', 'member_role', 'brokerage'):
            s = Store().accepted()
            if change == 'profile_role': s.profile['role'] = 'investor'
            elif change == 'admin': s.profile['is_brokerage_admin'] = True
            elif change == 'member_role': s.member['role'] = 'owner'
            else: s.profile['brokerage_id'] = 'other-brokerage'
            with self.subTest(change=change), self.assertRaises((PermissionError, ValueError)): self.call(s)
            self.assertEqual(s.writes, [])

    def test_inactive_brokerage_is_denied_even_for_an_existing_agent(self):
        for accepted in (False, True):
            s = Store().accepted(); s.brokerage['is_active'] = False
            if not accepted: s.invite.update(status='pending', accepted_by=None)
            with self.subTest(accepted=accepted), self.assertRaises(ValueError): self.call(s)
            self.assertEqual(s.writes, [])

    def test_existing_accepted_connection_is_not_a_new_expired_invitation(self):
        s = Store().accepted(); s.invite['expires_at'] = '2020-01-01T00:00:00Z'
        self.assertTrue(self.call(s)['accepted']); self.assertEqual(s.writes, [])

    def test_empty_writes_never_consume_an_invite_or_claim_success(self):
        for field in ('profile', 'member', 'invite'):
            s = Store(); s.empty_once = field
            with self.subTest(field=field), self.assertRaises(RuntimeError): self.call(s)
            self.assertEqual(s.invite['status'], 'pending')

    def test_actual_http_handler_allows_safe_repeated_acceptance(self):
        s = Store()
        first = self.call(s, handler=True)
        writes = len(s.writes)
        second = self.call(s, handler=True)
        self.assertEqual(first, (200, {'ok': True, 'membership': {'brokerageId': BROKERAGE, 'accepted': True}}))
        self.assertEqual(second, first)
        self.assertEqual(len(s.writes), writes)
