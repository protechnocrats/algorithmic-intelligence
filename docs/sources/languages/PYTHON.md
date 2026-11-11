# Sources for `skills/algorithmic-intelligence/references/languages/PYTHON.md`

Where each claim in that file comes from, for maintainers and reviewers. Not part of the installed skill. Documentation pages are under docs.python.org/3/ followed by the path given. Source paths are in github.com/python/cpython.

## Built-in structures

- Operation costs of `list`, `dict`, `set`, `deque`: wiki.python.org/moin/TimeComplexity (a community wiki describing CPython, not a language guarantee).
- `dict` insertion order (3.7): `library/stdtypes.html#mapping-types-dict`. String hashes keyed per process and `PYTHONHASHSEED`: `using/cmdline.html#envvar-PYTHONHASHSEED`.
- `Counter.most_common`, `defaultdict`, `deque` (`maxlen`), `OrderedDict` (`move_to_end`, `popitem(last=False)`): `library/collections.html`. `most_common(k)` using `heapq.nlargest`: Lib/collections/__init__.py.
- `heapq` (min-heap, `heapify` in linear time, `nsmallest`): `library/heapq.html`.
- `bisect` with `key=` (3.10): `library/bisect.html`.
- `array`, `bytearray`, `memoryview`: `library/array.html` and `library/stdtypes.html#binary-sequence-types-bytes-bytearray-memoryview`.
- `int` digits of 30 bits: Include/cpython/longintrepr.h (`PyLong_SHIFT`).
- `functools.lru_cache` and `cache` (3.9): `library/functools.html`. `graphlib.TopologicalSorter` (3.9): `library/graphlib.html`. `itertools` (`pairwise` 3.10, `batched` 3.12, `groupby` grouping consecutive keys): `library/itertools.html`. `heapq.merge`: `library/heapq.html#heapq.merge`.
- Free-threaded CPython (3.13): `howto/free-threading-python.html`.

## Packages

- sortedcontainers and its last release: grantjenks.com/docs/sortedcontainers and pypi.org/project/sortedcontainers ("Release history").
- more-itertools (`unique_everseen`, `unique_justseen`, `minmax`, `argmin`, `argmax`, `sort_together`): more-itertools.readthedocs.io/en/stable/api.html.
- cachetools (thread safety and `lock`, exceptions not cached, keyword arguments keyed separately, lazy TTL expiry): cachetools.readthedocs.io (sections "Cache implementations" and "Memoizing decorators").
- bitarray (`frozenbitarray`, shift behavior): github.com/ilanschnell/bitarray, README "Reference".

## Hidden costs

- String `+=` buffer reuse as a CPython detail: `library/stdtypes.html#common-sequence-operations`, note 6.
- `key=` called once per element, `cmp_to_key`: `howto/sorting.html`.
- `statistics.mean` exact arithmetic and `fmean` (3.8): `library/statistics.html`.
- Dataclass `__hash__` building a tuple each call: Lib/dataclasses.py (`_hash_add`); hashing rules for `eq` and `frozen`: `library/dataclasses.html#module-contents` (`unsafe_hash`). Tuple hash cache (3.14): Include/cpython/tupleobject.h (`ob_hash`) and Objects/tupleobject.c.
- `copy.deepcopy`: `library/copy.html`.
- Recursion limit and the risk of raising it: `library/sys.html#sys.setrecursionlimit`.
- The global interpreter lock and threads: `glossary.html#term-global-interpreter-lock`.

## Input handling and security

- `int()` accepting Unicode decimal digits, whitespace, signs, and underscores (3.6): `library/functions.html#int`. `float()` and `"nan"`, `"inf"`: `library/functions.html#float`. `str.isdigit`: `library/stdtypes.html#str.isdigit`. `\d` matching Unicode digits: `library/re.html` ("\d").
- `re.escape`: `library/re.html#re.escape`. `re` backtracking with no time limit: Python has no published statement; implementation behavior (Modules/_sre).
- `pickle`, `marshal`, `shelve` warnings: the warning at the top of `library/pickle.html`, `library/marshal.html`, `library/shelve.html`. `yaml.load`: PyYAML documentation, pyyaml.org/wiki/PyYAMLDocumentation ("Loading YAML").
- `json` and deep nesting: Modules/_json.c (recursion through `Py_EnterRecursiveCall`); implementation behavior.
- Case mapping and length changes: `library/stdtypes.html#str.upper`, `#str.casefold`. `unicodedata.normalize`: `library/unicodedata.html`.

## Bit manipulation

- `int.bit_count` (3.10), `bit_length`: `library/stdtypes.html#int.bit_count`. Bitwise operations on integers: `library/stdtypes.html#bitwise-operations-on-integer-types`.
- `array` and `struct` raising on out-of-range values: `library/array.html` and `library/struct.html`.
- NumPy integer overflow (arrays wrap, scalars warn, out-of-bounds Python integers raise in NumPy 2): numpy.org/doc/stable/user/basics.types.html ("Overflow errors") and the NumPy 2.0 migration guide (numpy.org/doc/stable/numpy_2_0_migration_guide.html).

## Python-specific traps

- Hashing of numeric types (`1`, `1.0`, `True` equal; `hash(n)` modulo 2⁶¹ − 1; `hash(-1) == -2`): `library/stdtypes.html#hashing-of-numeric-types`.
- Sort stability and `reverse=True`: `howto/sorting.html` ("Sort Stability and Complex Sorts"). `max`/`min` returning the first extreme: `library/functions.html#max`.
- `defaultdict` inserting on lookup: `library/collections.html#collections.defaultdict.__missing__`.
- Iterator exhaustion: `library/stdtypes.html#iterator-types`. `zip(strict=True)` (3.10): `library/functions.html#zip`.
- Compensated float `sum()` (3.12): `library/functions.html#sum`. `math.fsum`: `library/math.html#math.fsum`. `round` half to even: `library/functions.html#round`.
- Floor division and modulo: `reference/expressions.html#binary-arithmetic-operations`.
- Integer string conversion limit: `library/stdtypes.html#int-max-str-digits`.
- `lru_cache` on methods keeping instances alive: `faq/programming.html#how-do-i-cache-method-calls`.

## Testing and benchmarking

- pytest loading `conftest.py` and plugins: docs.pytest.org ("Writing plugins", "conftest.py: local per-directory plugins").
- Hypothesis stateful testing: hypothesis.readthedocs.io ("Stateful testing").
- `cProfile`: `library/profile.html`. `tracemalloc`: `library/tracemalloc.html`. `timeit`: `library/timeit.html`. pyperf: pyperf.readthedocs.io.
- CrossHair and `crosshair diffbehavior`: crosshair.readthedocs.io ("diffbehavior"). Nagini: github.com/marcoeilers/nagini.
- `hmac.compare_digest`: `library/hmac.html#hmac.compare_digest`. `secrets.compare_digest`: `library/secrets.html`.
