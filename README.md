
# aiofiledol
aiofile (async filesys operations) with a simple (dict-like or list-like) interface


To install:	```pip install aiofiledol```


Get the bytes contents of the file k.

```python
>>> import os
>>> from aiofiledol import AioFileBytesReader
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
```

Set the contents of file ``k`` to be some bytes.

```python
>>> from aiofiledol import AioFileBytesPersister
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
```
