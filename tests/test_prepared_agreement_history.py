"""Owner-only read pages keep old agreement clients compatible and private."""
import asyncio
import copy
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('prepared_history', ROOT / 'api/admin-dashboard.py')
API = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(API)
OWNER = '11111111-1111-4111-8111-111111111111'


class PreparedAgreementHistoryTests(unittest.TestCase):
    def row(self, index=0):
        return {'id':str(index), 'form_code':'TXR-1507', 'client_names':['QA Client'],
                'status':'signed', 'signwell_document_id':'qa-document',
                'agreement_data':{'privateAnswer':'not returned'}}

    def test_bounded_page_keeps_owner_scope_tie_order_and_response_contract(self):
        rows = [self.row(i) for i in range(101)]
        original = copy.deepcopy(rows)
        with patch.object(API, '_get', AsyncMock(return_value=rows)) as get:
            result = asyncio.run(API._standalone_agreement_page({'id':OWNER}, '100'))
        query = get.await_args.args[0]
        self.assertIn('agent_user_id=eq.'+OWNER,query)
        self.assertIn('order=updated_at.desc,id.desc&offset=100&limit=101',query)
        self.assertEqual(len(result['agreements']),100)
        self.assertEqual(result['pagination'],{'hasMore':True,'nextOffset':200})
        self.assertIn('signingEnabled',result)
        self.assertIn('signingFormCodes',result)
        for row in result['agreements']:
            self.assertNotIn('agreement_data',row)
            self.assertFalse(row['canRetrySavedRequest'])
        self.assertEqual(rows,original)

    def test_exactly_full_short_and_empty_final_pages_need_no_extra_request(self):
        for size in (0,1,99,100):
            with self.subTest(size=size), patch.object(API, '_get', AsyncMock(return_value=[self.row(i) for i in range(size)])):
                result=asyncio.run(API._standalone_agreement_page({'id':OWNER}))
                self.assertEqual(len(result['agreements']),size)
                self.assertEqual(result['pagination'],{'hasMore':False,'nextOffset':None})

    def test_invalid_page_and_owner_never_query_private_documents(self):
        with patch.object(API, '_get', AsyncMock()) as get:
            for offset in (-1,1000001,'0&agent_user_id=eq.other','1.5',1.5,True,None,'',[], '9'*100):
                with self.subTest(offset=offset), self.assertRaises(ValueError):
                    asyncio.run(API._standalone_agreement_page({'id':OWNER},offset))
            with self.assertRaises(ValueError):
                asyncio.run(API._standalone_agreement_page({'id':'../other'}))
        get.assert_not_awaited()

    def test_page_never_advertises_an_out_of_range_next_offset(self):
        for offset in (0,100,999900,999950,1000000):
            with self.subTest(offset=offset), patch.object(API, '_get', AsyncMock(return_value=[self.row(i) for i in range(101)])):
                result=asyncio.run(API._standalone_agreement_page({'id':OWNER},offset))
                next_offset=result['pagination']['nextOffset']
                if next_offset is not None:
                    self.assertGreater(next_offset,offset)
                    self.assertLessEqual(next_offset,1000000)
                else:
                    self.assertFalse(result['pagination']['hasMore'])

    def test_malformed_store_result_is_not_mistaken_for_end_of_history(self):
        for rows in (None,{},[None]):
            with self.subTest(rows=rows), patch.object(API, '_get', AsyncMock(return_value=rows)):
                with self.assertRaises(RuntimeError):
                    asyncio.run(API._standalone_agreement_page({'id':OWNER}))

    def request(self, path, user=None, error=None):
        fake=SimpleNamespace(path=path,headers={})
        with patch.object(API, 'SUPABASE_URL', 'https://qa.example.test'), \
             patch.object(API, 'SUPABASE_SERVICE_ROLE_KEY', 'qa-key'), \
             patch.object(API, '_verified_user', AsyncMock(return_value=user)), \
             patch.object(API, '_standalone_agreement_page', AsyncMock(return_value={'agreements':[]},side_effect=error)) as page, \
             patch.object(API, '_json') as output:
            API.handler.do_GET(fake)
        return page,output

    def test_real_get_route_forwards_page_after_authentication_and_sanitizes_failure(self):
        page,output=self.request('/api/admin-dashboard?scope=standalone_agreements&offset=200',user={'id':OWNER})
        page.assert_awaited_once_with({'id':OWNER},'200')
        self.assertEqual(output.call_args.args[1],200)
        _,output=self.request('/api/admin-dashboard?scope=standalone_agreements',user={'id':OWNER},error=RuntimeError('PRIVATE key'))
        self.assertEqual(output.call_args.args[1],503)
        self.assertNotIn('PRIVATE',str(output.call_args))

    def test_signed_out_route_never_reads_a_page(self):
        page,output=self.request('/api/admin-dashboard?scope=standalone_agreements&offset=200')
        page.assert_not_awaited()
        self.assertEqual(output.call_args.args[1],401)
