"""Request-local hashes of the exact source bytes used by the packet renderer."""
from contextlib import contextmanager
from contextvars import ContextVar
import hashlib
from pathlib import Path

_active_sources = ContextVar('hof_pdf_sources', default=None)


@contextmanager
def collect_source_hashes():
    sources = []
    token = _active_sources.set(sources)
    try:
        yield sources
    finally:
        _active_sources.reset(token)


def audited_source_bytes(path):
    sources = _active_sources.get()
    if sources is None:
        return None
    data = Path(path).read_bytes()
    sources.append(hashlib.sha256(data).hexdigest())
    return data
