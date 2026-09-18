"""Shared embedded-font fallback and matching layout metrics for PDF text.

Stored answers are never modified. Canonically equivalent accents are composed
only for display. Font assets are local and loaded only when required.
"""
from functools import lru_cache
from itertools import groupby
from pathlib import Path
from threading import RLock
import unicodedata
from xml.sax.saxutils import escape

from reportlab.pdfbase import pdfmetrics, _glyphlist
from reportlab.pdfbase.ttfonts import TTFont


FONT_DIR = Path(__file__).resolve().parent / 'fonts'
FALLBACKS = (('HOFUnicode', 'NotoSans-Regular.ttf'),
             ('HOFUnicodeSC', 'HOFUnicodeSC-Regular.ttf'))
_FONT_LOCK = RLock()


def display_text(value):
    return unicodedata.normalize('NFC', str(value if value is not None else ''))


@lru_cache(maxsize=8)
def _standard_characters(font):
    return frozenset(_glyphlist._glyphname2unicode[name]
                     for name in pdfmetrics.getFont(font).encoding.vector
                     if name in _glyphlist._glyphname2unicode)


def _fallback_font(name, filename):
    with _FONT_LOCK:
        if name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(name, str(FONT_DIR / filename)))
        return pdfmetrics.getFont(name)


@lru_cache(maxsize=8192)
def _character_font(character, base_font):
    if character in '\r\n\t' or ord(character) in _standard_characters(base_font):
        return base_font
    for name, filename in FALLBACKS:
        if ord(character) in _fallback_font(name, filename).face.charToGlyph:
            return name
    # Never silently replace a person's name or an entered contract term with
    # a box. This is a rendering error, not an instruction to rewrite names.
    raise ValueError('Some text contains characters the document cannot display correctly. '
                     'Please contact support before sending this document.')


def font_runs(value, base_font='Helvetica'):
    text = display_text(value)
    if not text:
        return []
    return [(font, ''.join(characters)) for font, characters in
            groupby(text, key=lambda character: _character_font(character, base_font))]


def text_width(value, base_font, size):
    return sum(pdfmetrics.stringWidth(text, font, size) for font, text in font_runs(value, base_font))


def draw_text(canvas, value, x, y, size, base_font='Helvetica'):
    text_object = canvas.beginText(x, y)
    for font, text in font_runs(value, base_font):
        text_object.setFont(font, size)
        text_object.textOut(text)
    canvas.drawText(text_object)


def paragraph_markup(value, base_font='Helvetica'):
    output = []
    text = display_text(value).replace('\r\n', '\n').replace('\r', '\n')
    for font, run in font_runs(text, base_font):
        safe = escape(run).replace('\n', '<br/>')
        output.append(safe if font == base_font else f'<font name="{font}">{safe}</font>')
    return ''.join(output)
