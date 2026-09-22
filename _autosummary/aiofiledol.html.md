# aiofiledol

aiofile (async filesys operations) with a simple (dict-like or list-like) interface

### Classes

| [`AioFileBytesPersister`](#aiofiledol.AioFileBytesPersister)(\*args[, delete_func])     | Async file persister with configurable deletion.   |
|---------------------------------------------------------------------------------------------------|----------------------------------------------------|
| [`AioFileBytesReader`](#aiofiledol.AioFileBytesReader)(rootdir[, subpath, ...])      |                                                    |
| [`AioFileStringPersister`](#aiofiledol.AioFileStringPersister)(\*args[, delete_func])    |                                                    |
| [`AioFileStringReader`](#aiofiledol.AioFileStringReader)(rootdir[, subpath, ...])     |                                                    |
| [`RelPathAioFileBytesReader`](#aiofiledol.RelPathAioFileBytesReader)(rootdir[, ...])        |                                                    |
| [`RelPathFileStringReader`](#aiofiledol.RelPathFileStringReader)(rootdir[, subpath, ...]) |                                                    |

### *class* aiofiledol.AioFileBytesPersister(\*args, delete_func=None, \*\*kwargs)

Bases: `LocalFileDeleteMixin`, [`AioFileBytesReader`](#aiofiledol.AioFileBytesReader), `KvPersister`

Async file persister with configurable deletion.

### Examples

```pycon
>>> from dol.filesys import mk_tmp_dol_dir
>>> rootdir = mk_tmp_dol_dir('aiofiledol_test')
>>> # Default: safe trash with warning on fallback
>>> store = AioFileBytesPersister(rootdir)
>>> # Permanent deletion without warnings
>>> from dol.trash import permanent_delete
>>> store = AioFileBytesPersister(rootdir, delete_func=permanent_delete)
```

#### asetitem(k, v)

Write bytes `v` to the file at key `k` (async).

```pycon
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
```

### *class* aiofiledol.AioFileBytesReader(rootdir, subpath='', pattern_for_field=None, max_levels=None, , include_hidden=False, assert_rootdir_existence=False)

Bases: `FileCollection`, `KvReader`

#### *async* aget(k)

Get the bytes contents of the file `k`.

Async examples are driven with `asyncio.run` so they run under a
plain `--doctest-modules` collection (top-level `await` is a
syntax error in doctests).

```pycon
>>> import asyncio, os
>>> from dol.filesys import mk_tmp_dol_dir
>>> rootdir = mk_tmp_dol_dir('aiofiledol_test')
>>> filepath = os.path.join(rootdir, 'greeting')
>>> with open(filepath, 'wb') as fp:
...     _ = fp.write(b'hello world')
>>> s = AioFileBytesReader(rootdir, max_levels=0)
>>> asyncio.run(s.aget(filepath))
b'hello world'
```

### *class* aiofiledol.AioFileStringPersister(\*args, delete_func=None, \*\*kwargs)

Bases: [`AioFileBytesPersister`](#aiofiledol.AioFileBytesPersister)

### *class* aiofiledol.AioFileStringReader(rootdir, subpath='', pattern_for_field=None, max_levels=None, , include_hidden=False, assert_rootdir_existence=False)

Bases: [`AioFileBytesReader`](#aiofiledol.AioFileBytesReader)

### *class* aiofiledol.RelPathAioFileBytesReader(rootdir, subpath='', pattern_for_field=None, max_levels=None, , include_hidden=False, assert_rootdir_existence=False)

Bases: `PrefixRelativizationMixin`, `Store`

#### is_valid_key(k, \*args, \_\_name='is_valid_key', \*\*kwargs)

`is_valid_key` on the inner key – see `mk_relative_path_store`.

#### validate_key(k, \*args, \_\_name='validate_key', \*\*kwargs)

`validate_key` on the inner key – see `mk_relative_path_store`.

### *class* aiofiledol.RelPathFileStringReader(rootdir, subpath='', pattern_for_field=None, max_levels=None, , include_hidden=False, assert_rootdir_existence=False)

Bases: `PrefixRelativizationMixin`, `Store`

#### is_valid_key(k, \*args, \_\_name='is_valid_key', \*\*kwargs)

`is_valid_key` on the inner key – see `mk_relative_path_store`.

#### validate_key(k, \*args, \_\_name='validate_key', \*\*kwargs)

`validate_key` on the inner key – see `mk_relative_path_store`.
