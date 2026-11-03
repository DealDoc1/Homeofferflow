"""Value-free diagnostics for rejected SignWell create requests.

Provider error strings may echo names, answers, PDFs, or credentials. Only
known schema field paths and locally defined categories cross this boundary.
"""
import re

from lib.signwell_delivery import DeliveryUnsent


ROOTS = frozenset({'files', 'recipients', 'fields', 'checkbox_groups',
    'conditional_rules', 'metadata', 'name', 'subject', 'message', 'draft',
    'test_mode', 'api_application_id', 'embedded_signing', 'embedded',
    'with_signature_page', 'custom_requester_name', 'custom_requester_email'})
MEMBERS = frozenset({'id', 'name', 'email', 'recipient_id', 'type', 'page',
    'x', 'y', 'width', 'height', 'required', 'value', 'api_id', 'file_url',
    'file_base64', 'date_format', 'lock_sign_date', 'fixed_width', 'validation',
    'validation_regex', 'label', 'delivery_method', 'phone_number', 'fields',
    'min', 'max', 'selection_requirement', 'field_ids'})


def safe_field_path(value):
    if not isinstance(value, str) or len(value) > 160:
        return None
    # Normalize common bracket notation without retaining provider values.
    path = re.sub(r'\[(\d{1,4})\]', r'.\1', value)
    parts = path.split('.')
    if not parts or parts[0] not in ROOTS or len(parts) > 8:
        return None
    if any(part not in MEMBERS and not re.fullmatch(r'\d{1,4}', part) for part in parts[1:]):
        return parts[0]  # Unknown nested keys can themselves contain client data.
    return '.'.join(parts)


def rejection_diagnostic(response):
    status = int(response.status_code)
    fields = set()
    try:
        # No raw body, provider message, exception, headers, or values are logged.
        raw = getattr(response, 'content', b'')
        data = response.json() if not isinstance(raw, bytes) or len(raw) <= 65536 else {}
        errors = data.get('errors') if isinstance(data, dict) else None
        if isinstance(errors, dict):
            remaining = 64

            def visit(value, prefix=''):
                nonlocal remaining
                if remaining <= 0:
                    return
                remaining -= 1
                if isinstance(value, dict):
                    for key, child in value.items():
                        if remaining <= 0:
                            break
                        remaining -= 1
                        if not isinstance(key, str):
                            continue
                        raw_path = prefix + '.' + key if prefix else key
                        path = safe_field_path(raw_path)
                        if not path:
                            continue
                        # Unknown keys collapse to their root. Do not traverse
                        # their values or retain private key fragments.
                        if path == path.split('.')[0] and raw_path != path:
                            fields.add(path)
                            continue
                        visit(child, path)
                elif isinstance(value, list) and any(isinstance(item, (dict, list)) for item in value[:64]):
                    for index, child in enumerate(value[:64]):
                        path = safe_field_path(prefix + '.' + str(index))
                        if path:
                            visit(child, path)
                        if remaining <= 0:
                            break
                elif prefix:
                    fields.add(prefix)

            visit(errors)
        elif isinstance(errors, list):
            for error in errors[:64]:
                if isinstance(error, dict):
                    path = safe_field_path(error.get('field') or error.get('path'))
                    if path:
                        fields.add(path)
    except Exception:
        pass
    fields = sorted(fields)[:16]
    roots = {path.split('.')[0] for path in fields}
    category = 'request_rejected'
    if status in {401, 403}: category = 'service_authentication'
    elif status == 402: category = 'service_account'
    elif status == 413: category = 'packet_size'
    elif status == 429: category = 'rate_limit'
    elif status == 422:
        if roots & {'fields', 'checkbox_groups', 'conditional_rules'}: category = 'signature_fields'
        elif 'recipients' in roots: category = 'signer_details'
        elif 'files' in roots: category = 'packet_file'
        else: category = 'request_validation'
    return {'http_status': status, 'category': category, 'fields': fields}


class SigningCreateRejected(DeliveryUnsent):
    def __init__(self, response):
        self.diagnostic = rejection_diagnostic(response)
        self.code = 'signwell_' + self.diagnostic['category']
        reasons = {
            'signature_fields': 'The signing service rejected the signature-field setup.',
            'signer_details': 'The signing service could not accept the signer details. Check the names and email addresses.',
            'packet_file': 'The signing service could not accept the offer PDF.',
            'packet_size': 'The offer PDF is too large for the signing service.',
            'rate_limit': 'The signing service is busy. Wait a moment before retrying this saved offer.',
            'service_authentication': 'The signing connection needs attention.',
            'service_account': 'The signing-service account needs attention.',
        }
        reason = reasons.get(self.diagnostic['category'], 'The signing service could not prepare your offer.')
        super().__init__(reason + ' Your offer is saved. No invitation was requested.')
