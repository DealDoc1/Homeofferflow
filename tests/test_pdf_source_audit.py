"""Source manifests stay local to each renderer call, including failed calls."""
import asyncio
import hashlib
import unittest
from unittest.mock import patch

from lib.pdf_source_audit import collect_source_hashes, audited_source_bytes


class PdfSourceAuditTests(unittest.TestCase):
    def test_inactive_audit_preserves_existing_reader_path(self):
        with patch('pathlib.Path.read_bytes') as read:
            self.assertIsNone(audited_source_bytes('unused.pdf'))
            read.assert_not_called()

    def test_manifest_hashes_exact_bytes_returned_to_renderer(self):
        with patch('pathlib.Path.read_bytes', return_value=b'source bytes'):
            with collect_source_hashes() as sources:
                self.assertEqual(audited_source_bytes('source.pdf'), b'source bytes')
            self.assertEqual(sources, [hashlib.sha256(b'source bytes').hexdigest()])

    def test_nested_collection_restores_parent_without_mixing_sources(self):
        with patch('pathlib.Path.read_bytes', side_effect=[b'outer', b'inner', b'outer-2']):
            with collect_source_hashes() as outer:
                audited_source_bytes('outer.pdf')
                with collect_source_hashes() as inner:
                    audited_source_bytes('inner.pdf')
                audited_source_bytes('outer-2.pdf')
        self.assertEqual(len(outer), 2)
        self.assertEqual(inner, [hashlib.sha256(b'inner').hexdigest()])

    def test_failed_read_does_not_leak_collector(self):
        with patch('pathlib.Path.read_bytes', side_effect=OSError('unavailable')):
            with self.assertRaises(OSError):
                with collect_source_hashes():
                    audited_source_bytes('missing.pdf')
        self.assertIsNone(audited_source_bytes('outside.pdf'))

    def test_concurrent_tasks_have_separate_manifests(self):
        async def render(name):
            with collect_source_hashes() as sources:
                await asyncio.sleep(0)
                audited_source_bytes(name)
                await asyncio.sleep(0)
                return sources
        async def run():
            return await asyncio.gather(render('first'), render('second'))
        with patch('pathlib.Path.read_bytes', autospec=True, side_effect=lambda path: str(path).encode()):
            first, second = asyncio.run(run())
        self.assertEqual(first, [hashlib.sha256(b'first').hexdigest()])
        self.assertEqual(second, [hashlib.sha256(b'second').hexdigest()])
