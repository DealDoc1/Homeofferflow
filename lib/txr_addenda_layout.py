"""Lossless source-blank text and continuation layout for standalone addenda."""
from io import BytesIO
from pypdf import PdfReader
from lib.pdf_text import draw_text, text_width
from lib.repair_continuation import render_text_continuation, continuation_field


def clean(value):
    return ' '.join(str(value if value is not None else '').split())


def inline(value, blanks, size=8):
    value = clean(value)
    if not value:
        return []
    for half in range(int(size * 2), 13, -1):
        point_size, words, entries = half / 2, value.split(), []
        for x, y, width in blanks:
            line = []
            while words and text_width(' '.join(line + [words[0]]), 'Helvetica', point_size) <= width:
                line.append(words.pop(0))
            if line:
                entries.append((x, y, ' '.join(line), point_size))
        if not words:
            return entries
    return None


class SourceAnswers:
    def __init__(self, data, title, page_count):
        self.data, self.title = data, title
        self.pages = {page: [] for page in range(1, page_count + 1)}
        self.overflow = {}

    def put(self, value, blanks, label, *, page=1, size=8, visible=True):
        entries = inline(value, blanks, size)
        if entries is None:
            self.overflow[label] = clean(value)
            entries = inline('Exhibit', blanks[:1], 7)
            if entries is None:
                raise ValueError('Source blank cannot hold a continuation reference')
        if visible:
            self.pages[page].extend(entries)

    def names(self, page, rows, columns):
        for role, x, width in columns:
            for index, value in enumerate((self.data.get(role.lower() + '_names') or [])[:2]):
                self.put(value, [(x, rows[index], width)], f'{role} {index + 1}',
                         page=page, size=9, visible=not self.data.get('_for_signing'))

    def continuation(self):
        if not self.overflow:
            return None
        buyers = self.data.get('buyer_names') or []
        parties = {'property_address': clean(self.data.get('property_address')),
                   'buyer1': buyers[0] if buyers else '',
                   'buyer2': buyers[1] if len(buyers) > 1 else '',
                   # Purchase packets can identify a Seller without inviting
                   # that person to this Buyer-only signing request.
                   'seller': self.data.get('seller') or ' and '.join(self.data.get('seller_names') or [])}
        return render_text_continuation(parties, self.title,
            '\n\n'.join(label + ': ' + value for label, value in self.overflow.items()))

    def continuation_fields(self, start_page, prefix):
        continuation = self.continuation()
        if not continuation:
            return []
        buyer_count = len(self.data.get('buyer_names') or [])
        seller_count = len(self.data.get('seller_names') or [])
        fields = []
        for page in range(len(PdfReader(BytesIO(continuation)).pages)):
            for role, count in [('buyer', buyer_count), ('seller', seller_count)]:
                for index in range(count):
                    canonical = index + (1 if role == 'buyer' else 3)
                    recipient = index + 1 + (buyer_count if role == 'seller' else 0)
                    field = continuation_field(str(canonical), start_page + page, page + 1, prefix)
                    field['recipient_id'] = str(recipient)
                    field['api_id'] = f'{prefix}_continuation_{page + 1}_{role}{index + 1}_initials'
                    fields.append(field)
        return fields


def draw_entries(canvas, entries):
    for x, y, value, size in entries:
        draw_text(canvas, value, x, y, size)


def mark_cell(canvas, x, y):
    canvas.setFont('Helvetica-Bold', 6)
    canvas.drawCentredString(x, y - 2.15, 'X')
