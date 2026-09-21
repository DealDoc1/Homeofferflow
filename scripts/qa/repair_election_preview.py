"""Generate local-only synthetic specimens for the condition-election check."""
from pathlib import Path
from tests.test_controlled_launch import adapter, configure_local_forms, minimal_offer


def main():
    configure_local_forms()
    destination = Path('tmp/pdfs/repair-election')
    destination.mkdir(parents=True, exist_ok=True)
    for choice in ('yes', 'repairs'):
        offer = minimal_offer(
            buyer1='Example QA Buyer', seller='Example QA Seller',
            address='123 Example Street', asIs=choice,
            repairsText='Replace the cracked kitchen window before closing.')
        output = destination / f'condition-{choice}.pdf'
        output.write_bytes(adapter.fill_and_merge_20_19(offer))
        print(output)


if __name__ == '__main__':
    main()
