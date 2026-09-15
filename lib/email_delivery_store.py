"""Service-only Supabase storage for immutable Resend email requests.

Not activated by checkout yet. Requires the reviewed email-delivery schema
before integration. Never holds a database transaction open during email HTTP.
"""
import copy
import time

import httpx

from lib.email_delivery import EmailDeliveryPending


class EmailDeliveryStore:
    COLUMNS = 'delivery_key,payload,payload_fingerprint,status,first_attempt_at,provider_id'

    def __init__(self, *, supabase_url, service_key, client=None, clock=time.time):
        if not supabase_url or not service_key:
            raise EmailDeliveryPending('Email delivery tracking is unavailable.')
        self.url = supabase_url.rstrip('/') + '/rest/v1/hof_email_deliveries'
        self.headers = {'apikey': service_key, 'Authorization': 'Bearer ' + service_key,
                        'Content-Type': 'application/json', 'Prefer': 'return=representation'}
        self.client = client or httpx
        self.clock = clock

    def _rows(self, response):
        if response.status_code not in {200, 201}:
            raise EmailDeliveryPending('The email delivery record could not be saved or loaded.')
        try:
            rows = response.json()
        except Exception as error:
            raise EmailDeliveryPending('The email delivery record could not be confirmed.') from error
        if not isinstance(rows, list) or len(rows) > 1 or any(not isinstance(row, dict) for row in rows):
            raise EmailDeliveryPending('The email delivery record could not be confirmed.')
        return rows

    def _read(self, key):
        rows = self._rows(self.client.get(self.url, headers=self.headers, timeout=20,
                         params={'delivery_key': 'eq.' + key, 'select': self.COLUMNS, 'limit': '1'}))
        return rows[0] if rows else None

    def reserve(self, key, payload, fingerprint):
        row = self._read(key)
        if row:
            return row
        # ON CONFLICT DO NOTHING: a simultaneous checkout callback must read
        # the winner's immutable body, never overwrite it with regenerated PDF.
        rows = self._rows(self.client.post(self.url, timeout=20,
                         headers={**self.headers, 'Prefer': 'resolution=ignore-duplicates,return=representation'},
                         params={'on_conflict': 'delivery_key', 'select': self.COLUMNS},
                         json={'delivery_key': key, 'payload': copy.deepcopy(payload),
                               'payload_fingerprint': fingerprint, 'status': 'pending'}))
        row = rows[0] if rows else self._read(key)
        if not row:
            raise EmailDeliveryPending('The email request could not be confirmed. Nothing new was sent.')
        return row

    def begin_attempt(self, row):
        if row.get('first_attempt_at') is not None:
            return row
        rows = self._rows(self.client.patch(self.url, headers=self.headers, timeout=20,
                         params={'delivery_key': 'eq.' + row['delivery_key'], 'status': 'eq.pending',
                                 'first_attempt_at': 'is.null',
                                 'payload_fingerprint': 'eq.' + row['payload_fingerprint'],
                                 'select': self.COLUMNS},
                         json={'first_attempt_at': self.clock()}))
        # A concurrent callback may have stamped or completed it already.
        latest = rows[0] if rows else self._read(row['delivery_key'])
        if not latest:
            raise EmailDeliveryPending('The email attempt could not be confirmed. Nothing new was sent.')
        return latest

    def accept(self, row, provider_id):
        rows = self._rows(self.client.patch(self.url, headers=self.headers, timeout=20,
                         params={'delivery_key': 'eq.' + row['delivery_key'], 'status': 'eq.pending',
                                 'payload_fingerprint': 'eq.' + row['payload_fingerprint'],
                                 'first_attempt_at': 'eq.' + str(row['first_attempt_at']),
                                 'select': self.COLUMNS},
                         json={'status': 'accepted', 'provider_id': provider_id, 'payload': None}))
        latest = rows[0] if rows else self._read(row['delivery_key'])
        return bool(latest and latest.get('delivery_key') == row['delivery_key']
                    and latest.get('status') == 'accepted' and latest.get('provider_id') == provider_id
                    and latest.get('payload_fingerprint') == row['payload_fingerprint'])
