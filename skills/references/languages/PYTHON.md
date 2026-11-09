# References for `languages/PYTHON.md`

Sources for the claims in `languages/PYTHON.md`. Read only to verify a claim, on the page for the project's language and library version.

- Operation costs of built-in types: wiki.python.org/moin/TimeComplexity (a community wiki describing CPython, not a language guarantee); standard library: docs.python.org/3/library/
- Hashing of numeric types: docs.python.org/3/library/stdtypes.html#hashing-of-numeric-types
- Dataclass `__hash__` (`_hash_add`): Lib/dataclasses.py in github.com/python/cpython. Tuple hash cache (`ob_hash`, 3.14 and later): Include/cpython/tupleobject.h and Objects/tupleobject.c.
- Integer string conversion limit: docs.python.org/3/library/stdtypes.html#int-max-str-digits
- `key=` called exactly once per input record, `cmp_to_key`: docs.python.org/3/howto/sorting.html. Iterator exhaustion: docs.python.org/3/library/stdtypes.html.
- Packages: grantjenks.com/docs/sortedcontainers; github.com/more-itertools/more-itertools; cachetools.readthedocs.io; github.com/ilanschnell/bitarray; release data from pypi.org.
