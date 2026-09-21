"""Unsigned local fake-data previews; no provider requests or client files."""
from pathlib import Path
from tests.test_controlled_launch import adapter, configure_local_forms, minimal_offer
from tests.test_lease_terms_continuation import long_terms, lease_answers


def main():
    configure_local_forms()
    target = Path('tmp/pdfs/lease-terms-continuation')
    target.mkdir(parents=True, exist_ok=True)
    for kind in ('buyer','seller'):
        for name,text in [('short','Return the supplied keys and garage door controls.'),('long',long_terms(45))]:
            offer = minimal_offer(buyer1='Example QA Buyer',seller='Example QA Seller',
                address='123 Example Street', city='Example City', **lease_answers(kind),
                **{kind+'TemporaryLeaseSpecialProvisions':text})
            path = target/(kind+'-'+name+'.pdf')
            path.write_bytes(adapter.fill_and_merge_20_19(offer))
            print(path)


if __name__ == '__main__': main()
