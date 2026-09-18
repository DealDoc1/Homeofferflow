"""Unsigned synthetic identity/notice-field layout examples; never sends."""
from pathlib import Path
from tests.test_controlled_launch import adapter, configure_local_forms, minimal_offer
from tests.test_lease_terms_continuation import lease_answers


def main():
    configure_local_forms()
    target=Path('tmp/pdfs/lease-identity')
    target.mkdir(parents=True,exist_ok=True)
    for kind in ('buyer','seller'):
        for mode in ('short','long'):
            values=dict(buyer1='Example QA Buyer',seller='Example QA Seller',address='123 Example Street',city='Example City')
            if mode=='long':
                values.update(buyer1='Example Buyer With Additional Legal Names '*5+'BUYER-END',
                    seller='Example Seller With Additional Legal Names '*5+'SELLER-END',
                    address='987 '+('Example Long Road '*5).strip(),
                    buyerEmail='buyer'+'w'*54+'@example.com',sellerEmail='seller'+'w'*54+'@example.com')
            offer=minimal_offer(**{**lease_answers(kind),**values})
            path=target/(kind+'-'+mode+'.pdf')
            path.write_bytes(adapter.fill_and_merge_20_19(offer))
            print(path)


if __name__=='__main__':main()
