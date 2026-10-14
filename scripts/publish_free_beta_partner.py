"""Run only in the reviewed production job; never retrieve credentials locally."""
import asyncio
import json
import os
import sys
from lib.beta_partner_publication import publish


def main():
    url = str(os.environ.get('SUPABASE_URL') or '').rstrip('/')
    key = os.environ.get('SUPABASE_SECRET_KEY') or ''
    if url != 'https://acqylchftrjjoablvqyq.supabase.co':
        raise ValueError('Wrong production partner project.')
    if os.environ.get('BETA_CONFIRMATION') != 'PUBLISH_FREE_BETA':
        raise ValueError('Explicit free-beta publication was not selected.')
    if os.environ.get('GITHUB_ACTIONS') != 'true' or os.environ.get('GITHUB_REF') != 'refs/heads/main' or os.environ.get('GITHUB_REPOSITORY') != 'DealDoc1/Homeofferflow' or not os.environ.get('GITHUB_ACTOR'):
        raise ValueError('Publication runs only in reviewed protected production.')
    actor = 'Protected production job: ' + os.environ.get('GITHUB_ACTOR', '')
    result = asyncio.run(publish(url, key, os.environ.get('PARTNER_LEAD_ID'), actor))
    print(json.dumps(result))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        print('Free beta publication did not complete. Inspect the scoped partner record before retrying.', file=sys.stderr)
        raise SystemExit(1)
