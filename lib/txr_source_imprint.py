"""Remove only measured source-supplier contact imprints from known blanks.

This is not general PDF redaction. Exact source bytes, page/operation locations,
text hashes and isolated text-block structure must all match. It is called on
newly cloned blank pages before answer overlays, never on executed documents.
The original source file and copyright/form-identification text stay intact.
"""
import hashlib


# Source PDF bytes remain private. Hashes identify the reviewed originals;
# each page lists the two isolated TJ operations in its production imprint.
SOURCE_IMPRINTS = {
    'TXR-1501': ('d723f46e9cead0b6bf5ff288687475660f4246a54ebb874524d6cce11579f5dd',
                 ((71, 85),) * 5 + ((99, 113),)),
    'TXR-1506': ('df83ca9db03a72c22da12838254915c3b34a9a4ac7f057340c454b73bc0055b4',
                 ((71, 85),) * 5 + ((99, 113),)),
    'TXR-1507': ('ff3c3682f68036d502314ca6bb2230c28d8e0b1ca5a4a5d4816a66f9f415b46f',
                 ((71, 85), (99, 113))),
    'TXR-1508': ('b0c9a058a1333b4ee46f9fbaab2a54d306f8b087bca6d7c9b417ee95e52ede40',
                 ((99, 113),)),
    'TXR-1905': ('79f6b8e8b4faa8293abddf4e298f39dbaada703919812c01726c9721af5b0cf3',
                 ((99, 113),)),
    'TXR-1919': ('048dfe44ddd32b2106fbc07189f410ba554defb30ba6ab072ac420eddb10b27f',
                 ((71, 85), (99, 113))),
    'TXR-1953': ('00075ab42b6d7f234c5e70197f02fadb736b2ff3ee02a0dc1f5499535b045fc3',
                 ((99, 113),)),
    'TXR-1954': ('e96fe7d35245aee60920ba264ef870542199fa201e49382a6eac27718fabdc28',
                 ((99, 113),)),
}
IMPRINT_LINES = (
    ('21bceabce9ab2365bde6f9649f0f71c579a0129cd30fd52b1ad734987a76e52b', (34.015748, 25.875457)),
    ('82d77027d21dbe34f41a6f1018ba11b397c7ed71ec7eb375477ff7040724f82f', (34.015748, 17.37152)),
)


def remove_known_source_imprint(writer, source_bytes, form_code):
    """Edit writer-owned source pages in memory; return number of lines removed.

    Unknown/revised sources are left untouched, not heuristically scrubbed.
    Validate every page before editing any page. Replacing the content stream
    removes text from extraction too, rather than concealing it with a box.
    """
    spec = SOURCE_IMPRINTS.get(form_code)
    if not spec or hashlib.sha256(source_bytes).hexdigest() != spec[0]:
        return 0
    plan = spec[1]
    if len(writer.pages) != len(plan):
        raise ValueError('The reviewed source imprint does not match the document pages.')
    pending = []
    for page, indices in zip(writer.pages, plan):
        content = page.get_contents()
        operations = content.operations if content is not None else []
        if len(indices) != len(IMPRINT_LINES):
            raise ValueError('The reviewed source imprint is incomplete.')
        for index, (expected_hash, expected_position) in zip(indices, IMPRINT_LINES):
            if index < 2 or index + 1 >= len(operations):
                raise ValueError('The reviewed source imprint could not be identified.')
            operands, operator = operations[index]
            position, position_operator = operations[index - 1]
            isolated = operations[index - 2] == ([], b'BT') and operations[index + 1] == ([], b'ET')
            text = operands[0][0] if (operator == b'TJ' and len(operands) == 1
                                      and isinstance(operands[0], list) and len(operands[0]) == 1
                                      and isinstance(operands[0][0], str)) else None
            if (not isolated or position_operator != b'Td' or len(position) != 2
                    or any(abs(float(actual) - expected) > .00001 for actual, expected in zip(position, expected_position))
                    or text is None or hashlib.sha256(text.encode()).hexdigest() != expected_hash):
                raise ValueError('The reviewed source imprint could not be identified.')
        pending.append((page, content, [entry for index, entry in enumerate(operations) if index not in indices]))
    for page, content, operations in pending:
        content.operations = operations
        page.replace_contents(content)
    return sum(map(len, plan))
