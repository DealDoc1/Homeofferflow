"""Create synthetic unsigned inventory layout specimens locally only."""
from pathlib import Path
from tests.test_controlled_launch import adapter, configure_local_forms, minimal_offer
from tests.test_nonrealty_continuation import item_list
from tests.test_repair_continuation import long_terms


def main():
    configure_local_forms()
    target=Path('tmp/pdfs/nonrealty-continuation')
    target.mkdir(parents=True,exist_ok=True)
    for name,count,repairs in [('all-eleven-blanks',11,''),('overflow',70,''),('combined',12,long_terms())]:
        offer=minimal_offer(buyer1='Example QA Buyer',buyer2='Second QA Buyer',buyer2Email='second@example.com',
                            seller='Example QA Seller',address='123 Example Street',city='Example City',
                            nonRealtyItems='yes',nonRealtyAmount='500',nonRealtyDescription=item_list(count),
                            asIs='repairs' if repairs else 'yes',repairsText=repairs)
        output=target/(name+'.pdf')
        output.write_bytes(adapter.fill_and_merge_20_19(offer))
        print(output)


if __name__=='__main__':main()
