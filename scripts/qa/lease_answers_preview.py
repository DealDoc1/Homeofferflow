"""Local unsigned specimen for all overflowing lease-answer sections."""
from pathlib import Path
from tests.test_controlled_launch import adapter, configure_local_forms, minimal_offer
from tests.test_lease_terms_continuation import answer_key, lease_answers, long_answer, long_terms


def main():
    configure_local_forms()
    target=Path('tmp/pdfs/lease-answers')
    target.mkdir(parents=True,exist_ok=True)
    for kind in ('buyer','seller'):
        answers={answer_key(kind,section):long_answer(section,12) for section in ('utilities','pets')}
        answers[kind+'TemporaryLeaseSpecialProvisions']=long_terms(20)
        offer=minimal_offer(buyer1='Example QA Buyer',seller='Example QA Seller',
            address='123 Example Street',city='Example City',**lease_answers(kind),**answers)
        path=target/(kind+'.pdf')
        path.write_bytes(adapter.fill_and_merge_20_19(offer))
        print(path)


if __name__=='__main__':main()
