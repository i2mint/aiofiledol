"""
aiofile (async filesys operations) with a simple (dict-like or list-like) interface
"""

# TODO: Revise names to align with dol.filesys
import asyncio
import os

from dol import wrapped_self
from dol.base import KvReader, KvPersister
from dol.dig import inner_most_key
from dol.paths import mk_relative_path_store
from dol.filesys import (
    FileCollection,
    LocalFileDeleteMixin,
    validate_key_and_raise_key_error_on_exception,
)

from aiofile import AIOFile  # pip install aiofile

_dflt_not_valid_error_msg = (
    "Key not valid (usually because does not exist or access not permitted): {}"
)
_dflt_not_found_error_msg = "Key not found: {}"


def _resolve_key(store, k):
    """The leaf-level filepath for ``k``, resolved through any wrapping layers.

    ``mk_relative_path_store`` (and dol's wrapping machinery generally) wraps by
    delegation: a method defined on the wrapped class is reached bound to the INNER
    store, but with the OUTER, un-transformed key. Handing that key straight to
    ``AIOFile`` would resolve it against the process CWD instead of ``rootdir``.
    Walking the wrapper chain with ``inner_most_key`` recovers the real filepath.

    This REPLACES ``store._id_of_key(k)`` -- it walks the whole chain including the
    leaf, so the two must never be composed. For an un-wrapped store no layer defines
    ``_id_of_key`` and ``k`` is returned verbatim.
    """
    return inner_most_key(wrapped_self(store), k, default=k)


class AioFileBytesReader(FileCollection, KvReader):
    _read_open_kwargs = dict(mode="rb")

    __getitem__ = None

    # @validate_key_and_raise_key_error_on_exception  # TODO: does this also wrap the async?
    async def aget(self, k):  # noqa
        """Get the bytes contents of the file ``k``.

        Async examples are driven with ``asyncio.run`` so they run under a
        plain ``--doctest-modules`` collection (top-level ``await`` is a
        syntax error in doctests).

        >>> import asyncio, os
        >>> from dol.filesys import mk_tmp_dol_dir
        >>> rootdir = mk_tmp_dol_dir('aiofiledol_test')
        >>> filepath = os.path.join(rootdir, 'greeting')
        >>> with open(filepath, 'wb') as fp:
        ...     _ = fp.write(b'hello world')
        >>> s = AioFileBytesReader(rootdir, max_levels=0)
        >>> asyncio.run(s.aget(filepath))
        b'hello world'
        """

        async with AIOFile(_resolve_key(self, k), **self._read_open_kwargs) as fp:
            v = await fp.read()  # Question: Is it faster if we just did `return await fp.read(), instead of assign?
        return v
        # with open(k, **self._read_open_kwargs) as fp:
        #     return fp.read()


class AioFileBytesPersister(LocalFileDeleteMixin, AioFileBytesReader, KvPersister):
    """Async file persister with configurable deletion.

    Examples:
        >>> from dol.filesys import mk_tmp_dol_dir
        >>> rootdir = mk_tmp_dol_dir('aiofiledol_test')
        >>> # Default: safe trash with warning on fallback
        >>> store = AioFileBytesPersister(rootdir)
        >>> # Permanent deletion without warnings
        >>> from dol.trash import permanent_delete
        >>> store = AioFileBytesPersister(rootdir, delete_func=permanent_delete)
    """

    _write_open_kwargs = dict(mode="wb")

    def __init__(self, *args, delete_func=None, **kwargs):
        """Initialize async file persister.

        Args:
            *args: Passed to parent classes
            delete_func: Optional custom deletion function.
                If None, uses class default (safe trash with fallback).
            **kwargs: Passed to parent classes
        """
        super().__init__(*args, **kwargs)
        if delete_func is not None:
            self._delete_func = delete_func

    @validate_key_and_raise_key_error_on_exception
    async def asetitem(self, k, v):
        """Write bytes ``v`` to the file at key ``k`` (async).

        >>> import asyncio, os
        >>> from dol.filesys import mk_tmp_dol_dir
        >>> rootdir = mk_tmp_dol_dir('aiofiledol_test')
        >>> rpath = lambda *p: os.path.join(rootdir, *p)
        >>> s = AioFileBytesPersister(rootdir)
        >>> k = rpath('foo')
        >>> if k in s:
        ...     del s[k]  # delete key if present
        >>> n = len(s)  # number of items in store
        >>> asyncio.run(s.asetitem(k, b'bar'))
        >>> len(s) == n + 1  # there's one more item in store
        True
        >>> k in s
        True
        >>> asyncio.run(s.aget(k))  # read it back (async reader; __getitem__ is disabled)
        b'bar'
        """
        async with AIOFile(_resolve_key(self, k), **self._write_open_kwargs) as fp:
            await fp.write(v)
            await fp.fsync()

    def __setitem__(self, k, v):
        return asyncio.create_task(self.asetitem(k, v))

    # @validate_key_and_raise_key_error_on_exception
    # def __setitem__(self, k, v):
    #     with open(k, **self._write_open_kwargs) as fp:
    #         return fp.write(v)


RelPathAioFileBytesReader = mk_relative_path_store(
    AioFileBytesReader,
    prefix_attr="rootdir",
    __name__="RelPathAioFileBytesReader",
)


class AioFileStringReader(AioFileBytesReader):
    _read_open_kwargs = dict(AioFileBytesReader._read_open_kwargs, mode="rt")


class AioFileStringPersister(AioFileBytesPersister):
    _write_open_kwargs = dict(AioFileBytesPersister._write_open_kwargs, mode="wt")


RelPathFileStringReader = mk_relative_path_store(
    AioFileStringReader,
    prefix_attr="rootdir",
    __name__="RelPathFileStringReader",
)
