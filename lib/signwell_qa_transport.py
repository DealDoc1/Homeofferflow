"""Canonical JSON transport for fixed operator tests; never customer delivery.

Matches the official SDK's create/send paths. No retries, redirects, configurable
destination, logging, credentials lookup or journal mutation are implemented.
The coordinator owns reservation/readback/checkpoint sequencing.
"""
import uuid

CREATE_URL = 'https://www.signwell.com/api/v1/documents'
TRANSPORT_REVISION = 'canonical-json-test-header-2026-11-04-v2'


def validate_test_payload(payload):
    if not isinstance(payload, dict) or payload.get('test_mode') is not True:
        raise ValueError('Operator QA requires explicit test mode. Nothing was sent.')


def _headers(api_key, payload):
    validate_test_payload(payload)
    if not isinstance(api_key, str) or not api_key.strip():
        raise ValueError('The existing QA connection is unavailable. Nothing was sent.')
    return {'X-Api-Key': api_key, 'Accept': 'application/json',
            'Content-Type': 'application/json', 'X-TestMode-Enabled': 'true'}


async def create_qa_document(client, *, api_key, payload):
    return await client.post(CREATE_URL, headers=_headers(api_key, payload),
                             json=payload, follow_redirects=False)


async def send_verified_qa_draft(client, document_id, *, api_key, payload):
    try:
        document_id = str(uuid.UUID(str(document_id)))
    except (ValueError, AttributeError, TypeError):
        raise ValueError('The reserved QA document identity is invalid. Nothing was sent.') from None
    return await client.post(CREATE_URL + '/' + document_id + '/send',
                             headers=_headers(api_key, payload), json=payload, follow_redirects=False)
