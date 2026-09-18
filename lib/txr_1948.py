"""Private-source renderer for TXR-1948 appraisal-waiver review drafts."""

from io import BytesIO

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen.canvas import Canvas


PAGE_WIDTH = 612
PAGE_HEIGHT = 792
ADDRESS_FIELD = 'Street Address and City'
CHOICE_FIELDS = {
    'waiver': '1 WAIVER Buyer w aives Buyers right to terminate the contract under Paragraph 2B of the',
    'partial_waiver': '2 PARTIAL WAIVER Buyer w aives Buyers right to terminate the contract under Paragraph 2B',
    'additional_right': '3 ADDITIONAL',
}
TERM_FIELDS = {'partial_value': 'ii the opinion of value is',
               'additional_days': 'days after the Effective Date if',
               'additional_value': 'than'}


def _editable_values(source, data):
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
    values = {ADDRESS_FIELD: _clean(data.get('property_address'))}
    values.update({name: '/On' if key == choice else '/Off' for key, name in CHOICE_FIELDS.items()})
    values.update({name: _clean(data.get(key)) if (
        key == 'partial_value' and choice == 'partial_waiver'
        or key in ('additional_days', 'additional_value') and choice == 'additional_right'
    ) else '' for key, name in TERM_FIELDS.items()})
    return values


def _clean(value):
    return " ".join(str(value or "").strip().split())


def _draw(canvas, value, x, y, size=8):
    value = _clean(value)
    if value:
        canvas.setFont("Helvetica", size)
        canvas.drawString(x, y, value)


def _mark(canvas, x, y):
    canvas.setFont("Helvetica-Bold", 10)
    canvas.drawString(x, y, "X")


def render_txr_1948(source_pdf_bytes, data):
    """Overlay an unsigned TXR-1948 private review draft on its source PDF."""
    source = PdfReader(BytesIO(source_pdf_bytes))
    if len(source.pages) != 1:
        raise ValueError("TXR-1948 source must contain exactly one page.")
    editable_values = _editable_values(source, data)
    packet = BytesIO()
    canvas = Canvas(packet, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
    choice = data.get("appraisal_choice")
    if editable_values is None:
        _draw(canvas, data.get("property_address"), 228, 653, 9)
        if choice == "waiver":
            _mark(canvas, 49, 546)
        elif choice == "partial_waiver":
            _mark(canvas, 49, 466)
            _draw(canvas, data.get("partial_value"), 234, 402, 9)
        elif choice == "additional_right":
            _mark(canvas, 49, 344)
            _draw(canvas, data.get("additional_days"), 68, 322, 9)
            _draw(canvas, data.get("additional_value"), 128, 289, 9)
    if not data.get("_for_signing"):
        buyers = data.get("buyer_names") or []
        sellers = data.get("seller_names") or []
        _draw(canvas, buyers[0] if buyers else "", 48, 207, 9)
        _draw(canvas, sellers[0] if sellers else "", 322, 207, 9)
        if len(buyers) > 1:
            _draw(canvas, buyers[1], 48, 141, 9)
        if len(sellers) > 1:
            _draw(canvas, sellers[1], 322, 141, 9)
    canvas.showPage()
    canvas.save()
    packet.seek(0)
    overlay = PdfReader(packet)
    writer = PdfWriter()
    writer.clone_document_from_reader(source)
    writer.pages[0].merge_page(overlay.pages[0])
    if editable_values is not None:
        writer.update_page_form_field_values(None, editable_values, auto_regenerate=False)
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
            "x": 58,
            "y": 764,
            "recipient_id": "1",
            "required": True,
            "width": 336,
            "height": 26,
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
                "x": 58,
                "y": 852,
                "recipient_id": "2",
                "required": True,
                "width": 336,
                "height": 26,
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
    return [fields]
