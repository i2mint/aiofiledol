"""
aiofile (async filesys operations) with a simple (dict-like or list-like) interface
"""
# TODO: Revise names to align with dol.filesys
import asyncio
import os

from dol.base import KvReader, KvPersister
from dol.paths import mk_relative_path_store
from dol.filesys import (
    FileCollection,
    validate_key_and_raise_key_error_on_exception,
)

from aiofile import AIOFile  # pip install aiofile

_dflt_not_valid_error_msg = "Key not valid (usually because does not exist or access not permitted): {}"
_dflt_not_found_error_msg = "Key not found: {}"


class AioFileBytesReader(FileCollection, KvReader):
    _read_open_kwargs = dict(mode="rb")

    __getitem__ = None

    # @validate_key_and_raise_key_error_on_exception  # TODO: does this also wrap the async?
    async def aget(self, k):  # noqa
        """
        Gets the bytes contents of the file k.
        >>> import os
        >>> filepath = __file__
        >>> dirpath = os.path.dirname(__file__)  # path of the directory where I (the module file) am
        >>> s = AioFileBytesReader(dirpath, max_levels=0)
        >>>
        >>> ####### Get the first 9 characters (as bytes) of this module #####################
        >>> t = await s.aget(filepath)
        >>> t[:14]
        b'import asyncio'
        >>>
        >>> ####### Test key validation #####################
        >>> await s.aget('not_a_valid_key')  # this key is not valid since not under the dirpath folder
        Traceback (most recent call last):
            ...
        filesys.KeyValidationError: 'Key not valid (usually because does not exist or access not permitted): not_a_valid_key'
        >>>
        >>> ####### Test further exceptions (that should be wrapped in KeyError) #####################
        >>> # this key is valid, since under dirpath, but the file itself doesn't exist (hopefully for this test)
        >>> non_existing_file = os.path.join(dirpath, 'non_existing_file')
        >>> try:
        ...     await s.aget(non_existing_file)
        ... except KeyError:
        ...     print("KeyError (not FileNotFoundError) was raised.")
        KeyError (not FileNotFoundError) was raised.
        """

        async with AIOFile(k, **self._read_open_kwargs) as fp:
            v = (
                await fp.read()
            )  # Question: Is it faster if we just did `return await fp.read(), instead of assign?
        return v
        # with open(k, **self._read_open_kwargs) as fp:
        #     return fp.read()


class AioFileBytesPersister(AioFileBytesReader, KvPersister):
    _write_open_kwargs = dict(mode="wb")

    @validate_key_and_raise_key_error_on_exception
    async def asetitem(self, k, v):
        """

        >>> from dol.filesys import mk_tmp_dol_dir
        >>> import os
        >>>
        >>> rootdir = mk_tmp_dol_dir('test')
        >>> rpath = lambda *p: os.path.join(rootdir, *p)
        >>> s = AioFileBytesPersister(rootdir)
        >>> k = rpath('foo')
        >>> if k in s:
        ...     del s[k]  # delete key if present
        ...
        >>> n = len(s)  # number of items in store
        >>> await s.asetitem(k, b'bar')
        >>> assert len(s) == n + 1  # there's one more item in store
        >>> assert k in s
        >>> assert (await s[k]) == b'bar'
        """
        async with AIOFile(k, **self._write_open_kwargs) as fp:
            await fp.write(v)
            await fp.fsync()

    def __setitem__(self, k, v):
        return asyncio.create_task(self.asetitem(k, v))

    @validate_key_and_raise_key_error_on_exception
    def __delitem__(self, k):
        os.remove(k)

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
    _write_open_kwargs = dict(
        AioFileBytesPersister._write_open_kwargs, mode="wt"
    )


RelPathFileStringReader = mk_relative_path_store(
    AioFileStringReader,
    prefix_attr="rootdir",
    __name__="RelPathFileStringReader",
)
