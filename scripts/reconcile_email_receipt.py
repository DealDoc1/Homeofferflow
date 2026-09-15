"""Private operator tool: inspect by exact IDs; --apply saves a verified receipt.

Run from the repository with PYTHONPATH=.; supply existing service credentials
through the process environment, never flags. No dotenv discovery or secrets
logging. Without --apply the tool is read-only. No Resend POST is implemented.
"""
import argparse
import json
import os
import sys

import httpx

from lib.email_delivery import EmailDeliveryPending
from lib.email_delivery_store import EmailDeliveryStore
from lib.email_receipt_lookup import inspect_email_receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--delivery-key', required=True)
    parser.add_argument('--provider-id', required=True)
    parser.add_argument('--apply', action='store_true', help='Save acceptance only after an exact provider match.')
    args = parser.parse_args(argv)
    try:
        api_key = os.environ.get('RESEND_API_KEY')
        if not api_key:
            raise EmailDeliveryPending('The email lookup credential is not configured.')
        with httpx.Client(timeout=20, follow_redirects=False) as client:
            store = EmailDeliveryStore(supabase_url=os.environ.get('SUPABASE_URL'),
                service_key=os.environ.get('SUPABASE_SERVICE_ROLE_KEY'), client=client)

            def retrieve(provider_id):
                response = client.get('https://api.resend.com/emails/' + provider_id,
                                      headers={'Authorization': 'Bearer ' + api_key})
                if response.status_code != 200:
                    raise EmailDeliveryPending('The provider lookup did not succeed.')
                return response.json()

            result = inspect_email_receipt(key=args.delivery_key, provider_id=args.provider_id,
                read=store.read_receipt, accept=store.accept, retrieve=retrieve, apply=args.apply)
        print(json.dumps(result, sort_keys=True))
        return 0 if result['status'] in {'accepted', 'already_accepted', 'matched'} else 2
    except Exception:
        # Provider/database exceptions can contain URLs, tokens or email body.
        print(json.dumps({'status': 'lookup_failed', 'updated': False,
                          'message': 'Receipt not confirmed. Check service access and the supplied IDs.'}))
        return 1


if __name__ == '__main__':
    sys.exit(main())
