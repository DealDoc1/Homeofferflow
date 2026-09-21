"""Build the static regular CJK fallback once, not during request handling.

Requires fonttools 4.59.0 in the operator's build environment only.
Source and license provenance is recorded in lib/fonts/README.md.
"""
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont


def main():
    source = Path('tmp/font-sources/NotoSansSC-VF.ttf')
    font = instantiateVariableFont(TTFont(source), {'wght': 400}, inplace=True)
    names = {1:'HOF Unicode SC', 2:'Regular', 3:'HOFUnicodeSC-Regular-20260918',
             4:'HOF Unicode SC Regular', 6:'HOFUnicodeSC-Regular',
             16:'HOF Unicode SC', 17:'Regular'}
    for record in font['name'].names:
        if record.nameID in names:
            record.string = names[record.nameID].encode(record.getEncoding())
    font.recalcTimestamp = False
    font.save('lib/fonts/HOFUnicodeSC-Regular.ttf')


if __name__ == '__main__':
    main()
