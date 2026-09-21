"""Private-source renderer for TXR-1948 appraisal-waiver review drafts."""

from io import BytesIO

from pypdf import PdfReader, PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject, RectangleObject, create_string_object
from reportlab.pdfgen.canvas import Canvas
from lib.pdf_text import draw_text, text_width
from lib.txr_addenda_layout import SourceAnswers, draw_entries, mark_cell


PAGE_WIDTH = 612
PAGE_HEIGHT = 792
RENDER_REVISION = 'txr-1948-2026-09-18-answer-continuation-v2'
BUYER_SIGNATURE_BOXES = ((58, 764, 336, 26), (58, 852, 336, 26))
ADDRESS_FIELD = 'Street Address and City'
CHOICE_FIELDS = {
    'waiver': '1 WAIVER Buyer w aives Buyers right to terminate the contract under Paragraph 2B of the',
    'partial_waiver': '2 PARTIAL WAIVER Buyer w aives Buyers right to terminate the contract under Paragraph 2B',
    'additional_right': '3 ADDITIONAL',
}
TERM_FIELDS = {'partial_value': 'ii the opinion of value is',
               'additional_days': 'days after the Effective Date if',
               'additional_value': 'than'}
TEXT_BLANKS = {
    ADDRESS_FIELD: (226.7, 654, 347),
    TERM_FIELDS['partial_value']: (232.3, 401.5, 97.6),
    TERM_FIELDS['additional_days']: (67.4, 321.8, 40.5),
    TERM_FIELDS['additional_value']: (126.7, 289.2, 91),
}


def answer_layout(data):
    """One lossless layout for editable appearances, flat sources and maps."""
    answers = SourceAnswers(data, 'TXR-1948 - Appraisal Addendum Continuation', 1)
    answers.field_entries = {}
    choice = data.get('appraisal_choice')
    values = {ADDRESS_FIELD: (data.get('property_address'), 'Property address')}
    for key, label in [('partial_value', 'Partial-waiver appraisal value'),
                       ('additional_days', 'Additional termination period (days)'),
                       ('additional_value', 'Additional-right appraisal value')]:
        active = (key == 'partial_value' and choice == 'partial_waiver'
                  or key in ('additional_days', 'additional_value') and choice == 'additional_right')
        values[TERM_FIELDS[key]] = (data.get(key) if active else '', label)
    for field, (value, label) in values.items():
        start = len(answers.pages[1])
        answers.put(value, [TEXT_BLANKS[field]], label, size=9)
        answers.field_entries[field] = answers.pages[1][start:]
    start = len(answers.pages[1])
    answers.names(1, (193, 127), [('Buyer', 45, 248), ('Seller', 320, 234)])
    answers.preview_entries = answers.pages[1][start:]
    return answers


def _editable_values(source, data, answers=None):
    """Use canonical form values for the supplied interactive TREC 49-1 source."""
    fields = source.get_fields() or {}
    widgets = [ref for page in source.pages for ref in page.get('/Annots', [])
               if ref.get_object().get('/Subtype') == '/Widget']
    if not fields and not widgets:
        return None  # Legacy non-interactive library source.
    expected = {ADDRESS_FIELD, *CHOICE_FIELDS.values(), *TERM_FIELDS.values(),
                'Signature1', 'Signature2', 'Signature3', 'Signature4'}
    canonical = source.trailer['/Root'].get('/AcroForm', {}).get('/Fields', [])
    if set(fields) != expected or {ref.idnum for ref in canonical} != {ref.idnum for ref in widgets}:
        raise ValueError('TXR-1948 editable source fields do not match the supported form.')
    if any(fields[name].get('/V') for name in expected if name.startswith('Signature')):
        raise ValueError('Use an unsigned TXR-1948 source, not an executed agreement.')
    choice = data.get('appraisal_choice')
    answers = answers or answer_layout(data)
    values = {name: ' '.join(entry[2] for entry in entries)
              for name, entries in answers.field_entries.items()}
    values.update({name: '/On' if key == choice else '/Off' for key, name in CHOICE_FIELDS.items()})
    return values


def _text_appearances(writer, answers):
    """Embed the same Unicode-aware text used for flat-source overlays.

    The ordinary field updater resets text and sets button states. Supply
    canonical text and matching appearances here so a standard-font encoding
    cannot turn a Unicode address into missing glyphs. Widgets stay editable.
    """
    for ref in writer.pages[0].get('/Annots', []):
        widget = ref.get_object()
        name = widget.get('/T')
        if name not in answers.field_entries:
            continue
        value = ' '.join(entry[2] for entry in answers.field_entries[name])
        # pypdf 4.3.1 can serialize a newly created Unicode TextStringObject
        # without its UTF-16 marker. Re-reading must recover text, not bytes.
        widget[NameObject('/V')] = create_string_object(b'\xfe\xff' + value.encode('utf-16-be'))
        left, bottom, right, top = map(float, widget['/Rect'])
        width, height = right - left, top - bottom
        packet = BytesIO()
        canvas = Canvas(packet, pagesize=(width, height))
        for x, y, value, size in answers.field_entries[name]:
            if not (left <= x and x + text_width(value, 'Helvetica', size) <= right
                    and bottom <= y < top):
                raise ValueError('TXR-1948 editable source text bounds do not match the supported form.')
            draw_text(canvas, value, x - left, y - bottom, size)
        canvas.showPage()
        canvas.save()
        page = PdfReader(BytesIO(packet.getvalue())).pages[0]
        appearance = DecodedStreamObject()
        appearance.set_data(page.get_contents().get_data())
        appearance.update({NameObject('/Type'): NameObject('/XObject'),
                           NameObject('/Subtype'): NameObject('/Form'),
                           NameObject('/BBox'): RectangleObject((0, 0, width, height)),
                           NameObject('/Resources'): page['/Resources'].clone(writer)})
        # PDF streams must be indirect objects. An inline stream may remain
        # extractable by pypdf while a real viewer silently displays it blank.
        widget[NameObject('/AP')] = DictionaryObject({NameObject('/N'): writer._add_object(appearance)})


def render_txr_1948(source_pdf_bytes, data):
    """Overlay an unsigned TXR-1948 private review draft on its source PDF."""
    source = PdfReader(BytesIO(source_pdf_bytes))
    if len(source.pages) != 1:
        raise ValueError("TXR-1948 source must contain exactly one page.")
    answers = answer_layout(data)
    editable_values = _editable_values(source, data, answers)
    packet = BytesIO()
    canvas = Canvas(packet, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    choice = data.get("appraisal_choice")
    if editable_values is None:
        draw_entries(canvas, answers.pages[1])
        centers = {'waiver': (52.04, 548.42), 'partial_waiver': (51.4, 468.14),
                   'additional_right': (51.56, 346.22)}
        if choice in centers:
            mark_cell(canvas, *centers[choice])
    else:
        draw_entries(canvas, answers.preview_entries)
    canvas.showPage()
    canvas.save()
    packet.seek(0)
    overlay = PdfReader(packet)
    writer = PdfWriter()
    writer.clone_document_from_reader(source)
    writer.pages[0].merge_page(overlay.pages[0])
    if editable_values is not None:
        writer.update_page_form_field_values(None,
            {name: '' if name in TEXT_BLANKS else value for name, value in editable_values.items()},
            auto_regenerate=False)
        _text_appearances(writer, answers)
    continuation = answers.continuation()
    if continuation:
        writer.append(PdfReader(BytesIO(continuation)))
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def build_signwell_fields_txr1948(data, *, client_count=None):
    """Return the source-calibrated TXR-1948 execution fields.

    This one-page appraisal addendum is signed by the named Buyers and
    Sellers only.  SignWell uses a 96-DPI, top-origin letter page, while the
    source PDF uses a bottom-origin 612 by 792-point page.  The fields below
    sit *above* the four printed execution rules so completed signatures do
    not cover the Buyer/Seller captions below each line.
    """
    buyers = data.get("buyer_names") or []
    sellers = data.get("seller_names") or []
    if not (1 <= len(buyers) <= 2 and 1 <= len(sellers) <= 2):
        raise ValueError("TXR-1948 requires one or two Buyers and one or two Sellers.")

    fields = [
        {
            "api_id": "txr1948_buyer1_signature_p1",
            "type": "signature",
            "page": 1,
            "x": BUYER_SIGNATURE_BOXES[0][0],
            "y": BUYER_SIGNATURE_BOXES[0][1],
            "recipient_id": "1",
            "required": True,
            "width": BUYER_SIGNATURE_BOXES[0][2],
            "height": BUYER_SIGNATURE_BOXES[0][3],
        },
        {
            "api_id": "txr1948_seller1_signature_p1",
            "type": "signature",
            "page": 1,
            "x": 424,
            "y": 764,
            "recipient_id": str(len(buyers) + 1),
            "required": True,
            "width": 318,
            "height": 26,
        },
    ]
    if len(buyers) == 2:
        fields.append(
            {
                "api_id": "txr1948_buyer2_signature_p1",
                "type": "signature",
                "page": 1,
                "x": BUYER_SIGNATURE_BOXES[1][0],
                "y": BUYER_SIGNATURE_BOXES[1][1],
                "recipient_id": "2",
                "required": True,
                "width": BUYER_SIGNATURE_BOXES[1][2],
                "height": BUYER_SIGNATURE_BOXES[1][3],
            }
        )
    if len(sellers) == 2:
        fields.append(
            {
                "api_id": "txr1948_seller2_signature_p1",
                "type": "signature",
                "page": 1,
                "x": 424,
                "y": 852,
                "recipient_id": str(len(buyers) + 2),
                "required": True,
                "width": 318,
                "height": 26,
            }
        )
    fields.extend(answer_layout(data).continuation_fields(2, 'txr1948'))
    return [fields]
