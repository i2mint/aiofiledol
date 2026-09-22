"""Tests that relativized stores read the file they advertise, not a CWD lookalike.

``mk_relative_path_store`` wraps by delegation, so a method defined on the wrapped
class (such as ``aget``) is reached bound to the INNER store while still receiving
the OUTER, un-transformed key. Passing that relative key straight to ``AIOFile``
resolves it against the process CWD instead of the store's ``rootdir`` -- silently
returning the wrong bytes when a same-named file happens to sit in the CWD, and
raising ``FileNotFoundError`` for a key the store just enumerated when it does not.
"""

import asyncio
import os

from aiofiledol import (
    AioFileBytesReader,
    RelPathAioFileBytesReader,
    RelPathFileStringReader,
)

KEY = "greeting"
REAL = b"REAL STORE CONTENT"
DECOY = b"DECOY FROM CWD"


def _store_dir(tmp_path, name, content=None):
    """Make a directory under ``tmp_path``, optionally holding a ``KEY`` file.

    Returns the path with a trailing separator -- what the relativized stores want,
    so that the keys they yield carry no leading separator.
    """
    d = tmp_path / name
    d.mkdir()
    if content is not None:
        mode = "wb" if isinstance(content, bytes) else "wt"
        with open(d / KEY, mode) as fp:
            fp.write(content)
    return str(d) + os.sep


def test_relpath_aget_reads_the_store_not_the_cwd(tmp_path, monkeypatch):
    """A relative key must resolve against ``rootdir``, never against the CWD."""
    rootdir = _store_dir(tmp_path, "realstore", REAL)
    monkeypatch.chdir(_store_dir(tmp_path, "decoy", DECOY))

    s = RelPathAioFileBytesReader(rootdir)
    assert asyncio.run(s.aget(KEY)) == REAL


def test_relpath_aget_finds_every_key_it_enumerates(tmp_path, monkeypatch):
    """Every key the store yields must be readable -- no ``FileNotFoundError``."""
    rootdir = _store_dir(tmp_path, "realstore", REAL)
    monkeypatch.chdir(_store_dir(tmp_path, "elsewhere"))

    s = RelPathAioFileBytesReader(rootdir)
    assert list(s) == [KEY]
    for k in s:
        assert asyncio.run(s.aget(k)) == REAL


def test_relpath_string_reader_too(tmp_path, monkeypatch):
    """The text-mode relativized reader inherits the same ``aget``, so same rule."""
    rootdir = _store_dir(tmp_path, "realstore", REAL.decode())
    monkeypatch.chdir(_store_dir(tmp_path, "decoy", DECOY.decode()))

    s = RelPathFileStringReader(rootdir)
    assert asyncio.run(s.aget(KEY)) == REAL.decode()


def test_bare_reader_still_takes_absolute_keys(tmp_path, monkeypatch):
    """Regression guard: an un-wrapped store keeps its absolute-key behaviour."""
    rootdir = _store_dir(tmp_path, "realstore", REAL)
    monkeypatch.chdir(_store_dir(tmp_path, "elsewhere"))

    s = AioFileBytesReader(rootdir, max_levels=0)
    assert asyncio.run(s.aget(os.path.join(rootdir, KEY))) == REAL
