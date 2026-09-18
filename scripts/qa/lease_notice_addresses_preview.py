"""Fake unsigned notice-address layout previews; no external sends."""
from pathlib import Path
from tests.test_controlled_launch import adapter, configure_local_forms, minimal_offer
from tests.test_lease_terms_continuation import lease_answers


def main():
    configure_local_forms()
    target=Path('tmp/pdfs/lease-notice-addresses')
    target.mkdir(parents=True,exist_ok=True)
    for kind in ('buyer','seller'):
        for mode in ('wrapped','overflow'):
            count=3 if mode=='wrapped' else 8
            buyer='222 Example Buyer Road, '+('West Wing Example Office ' * count)+'Example City, TX 75001'
            seller='111 Example Seller Road, '+('West Wing Example Suite ' * count)+'Example City, TX 75002'
            offer=minimal_offer(buyer1='Example QA Buyer',seller='Example QA Seller',
                address='123 Example Street',city='Example City',buyerMailAddr=buyer,sellerMailAddr=seller,
                **lease_answers(kind))
            path=target/(kind+'-'+mode+'.pdf')
            path.write_bytes(adapter.fill_and_merge_20_19(offer))
            print(path)


if __name__=='__main__': main()
