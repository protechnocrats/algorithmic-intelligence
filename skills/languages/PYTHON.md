# Python

Record the interpreter and version (`requires-python`, `.python-version`, CI matrix). CPython is the default; PyPy's JIT, GraalPy, and free-threaded CPython (3.13+, no global interpreter lock) change which costs matter. Several APIs below are version-specific.

**Contents:** Built-in structures · Hidden costs · asyncio · Bit manipulation · Python-specific traps · Testing, profiling, and benchmarking · References

## Built-in structures

| Structure | API | Key costs | Notes |
|---|---|---|---|
| Dynamic array | `list` | index O(1), `append`/`pop()` amortized O(1), `insert(0, x)`/`pop(0)` O(n), `in`/`index`/`remove`/`count` O(n), slice copy O(k) | |
| Hash map | `dict` | O(1) expected | Insertion order guaranteed (3.7+). Bounded LRU without `OrderedDict`: `pop` then reassign on a hit, evict `next(iter(d))` |
| Hash set | `set`, `frozenset` | O(1) expected | No order guarantee; string order changes per process |
| Counting, grouping | `Counter`, `defaultdict` | O(1) expected per update | `most_common(k)` is O(n log k) |
| Double-ended queue | `collections.deque` | ends O(1); indexing toward the middle O(n) | `maxlen` gives a bounded ring buffer |
| Reorderable map | `OrderedDict` | `move_to_end`, `popitem(last=False)` O(1) | A bounded LRU cache without a dependency |
| Priority queue | `heapq` on a `list` | push/pop O(log n), `heapify` O(n), `nsmallest(k)` O(n log k) | Min-heap, not stable, no decrease-key |
| Sorted sequence | `bisect` on a `list` | search O(log n), `insort` O(n) | `key=` since 3.10; no balanced tree in the standard library |
| Compact arrays | `array.array`, `bytearray`, `memoryview` | O(1), no per-element objects | `memoryview` slices without copying |
| Arbitrary-size bitset | `int` | `&`, `\|`, `^` O(n/30) | Immutable: setting one bit copies the integer |
| Caching | `functools.lru_cache(maxsize=...)`, `cache` (3.9+) | O(1) expected | `cache` and `lru_cache(maxsize=None)` are unbounded (rule 1) |
| Topological order | `graphlib.TopologicalSorter` (3.9+) | O(V + E) | |
| Iterator tools | `itertools` (`accumulate`, `groupby`, `islice`, `pairwise` 3.10+, `batched` 3.12+), `heapq.merge` | Lazy, O(1) memory | `groupby` groups only consecutive equal keys |

Not in the standard library: O(log n)-insert sorted containers (`sortedcontainers`), tries, interval trees, fast single-bit bitsets (`bitarray`), vectorized arrays (NumPy). Compiling hot code (Cython, mypyc, Numba, a Rust or C extension) is a build change (rule 5).

### Packages

These are dependencies (rule 7): check the module's manifest first, and follow "When the best technique is not available" in `ALGORITHM-ARSENAL.md`.

| Package | Provides | Watch for |
|---|---|---|
| `sortedcontainers` | `SortedList`, `SortedDict`, `SortedSet` | Its last release was in 2021, so check that this is acceptable to the project |
| `more-itertools` | `unique_everseen`, `unique_justseen`, `minmax`, `argmin`, `argmax`, `sort_together` | No top-k helper: use `heapq.nsmallest` |
| `cachetools` | `LRUCache`, `TTLCache`, `LFUCache`, and the `cached` decorator | The cache classes are not thread-safe: pass `lock` to `cached`. Exceptions are never cached. `foo(1)` and `foo(a=1)` are cached separately. `TTLCache` removes expired items lazily |
| `bitarray` | `bitarray`, `frozenbitarray` (hashable) | Shifts keep the length, and a negative shift raises `ValueError` |

## Hidden costs

| Pattern | Cost | Fix |
|---|---|---|
| `x in items` on a list or `dict.values()` in a loop | O(n) per check | A `set` or `dict` built once (traps: hashability, order) |
| `if x in set(items)` in a loop | Rebuilds the set: still O(n) | Build it outside the loop |
| `pop(0)` or `insert(0, x)` | O(n) per call | `deque` |
| `result = result + [x]`, `sum(list_of_lists, [])`, `bytes +=` in a loop | O(n²) | `append`, `itertools.chain.from_iterable`, `bytearray` or `b"".join` |
| `s += piece` for strings in a loop | CPython often reuses the buffer, not guaranteed; quadratic on PyPy | `"".join(pieces)`, `io.StringIO` |
| `s[i:]` or `lst[1:]` in a loop or recursion | Each slice copies: O(n²) | Pass indices; `memoryview` for bytes |
| `bisect.insort` to keep a growing list sorted | O(n²) total | `heapq` if only the minimum matters; sort once; `sortedcontainers` (ask) |
| `sorted`, `min`, `max` over a collection in a loop | O(n log n) or O(n) per iteration | Sort once, a heap, or a running answer |
| `sorted(xs, key=cmp_to_key(cmp))` where `cmp` computes keys | `cmp` does its work for each comparison | A plain `key=` function, which runs exactly once per element |
| `statistics.mean` on large float data | Exact rational arithmetic, much slower | `statistics.fmean` (3.8+) or `sum/len`, which can change the last digits. (`median` sorts, O(n log n); it is not a mean) |
| `copy.deepcopy` in a loop | Walks the whole object graph | Copy only what changes |
| Deep recursion | `RecursionError` near 1000 frames, plus call overhead | An explicit stack; raising the limit can crash the interpreter on the C stack. A `RecursionError` on accepted input is an existing bug (rule 4) |
| CPU-bound threads with the global interpreter lock | No parallel speedup | Processes (pickling, side-effect order change), vectorization, or a free-threaded build: each is a behavior or build change (rule 5) |

### Input handling and security

- **Number parsing is lenient.** `int()` and `float()` accept any Unicode decimal digit (`int("٥") == 5`), surrounding whitespace, a sign, and underscores (`"1_000"`); `float()` also accepts `"nan"` and `"inf"`. `str.isdigit()` is true for `"²"`, which `int()` rejects. A fast parser or a `\d+` regex (Unicode by default) changes what is accepted.
- **`re` backtracks** with no time limit. Escape input in a pattern with `re.escape`.
- **Unsafe deserialization.** `pickle`, `marshal`, `shelve`, `yaml.load` without `SafeLoader`, and `eval` run code from data. `json` raises `RecursionError` on deeply nested input.
- **Case and normalization.** `lower()`, `upper()`, and `casefold()` ignore the locale but can change length (`"ß".upper() == "SS"`); `casefold()` and `lower()` differ. Visually equal text can differ until `unicodedata.normalize`.
- **Hidden inputs.** `datetime.now()` without a zone, `time.localtime`, `locale` formatting, and `strftime` read the process's zone and locale.

## asyncio

A blocking call (`time.sleep`, synchronous network, file, or database calls, heavy CPU work) inside a coroutine stalls the whole event loop. Turning `await` in a loop into `asyncio.gather` or a `TaskGroup` (3.11+) changes ordering, error behavior (sibling cancellation), and load on the callee: a behavior change, bounded with a `Semaphore`.

## Bit manipulation

| Operation | Python |
|---|---|
| And, or, xor, not, shifts | `&`, `\|`, `^`, `~` (`~x == -x - 1`), `<<`, `>>` (arithmetic; no logical shift) |
| Popcount | `x.bit_count()` (3.10+), else `bin(x).count("1")` |
| Highest bit, lowest set bit | `x.bit_length()`, `x & -x` |
| Fixed width | `int` never overflows: emulate wraparound with `& 0xFFFFFFFF` and sign conversion. NumPy wraps silently; `array` and `struct` raise. Moving arithmetic between them and `int` changes overflow behavior |

An `int` bitmask holds any number of flags, but every operation costs time proportional to its size and allocates. For many single-bit updates on a large set, a `bytearray` is faster.

## Python-specific traps

- **Order.** `dict` keeps insertion order; `set` does not. `list(dict.fromkeys(items))` deduplicates keeping first-occurrence order.
- **Hashability.** Replacing `in list` with a `set` raises `TypeError` for unhashable elements (lists, dicts, non-frozen dataclasses with `eq=True`, classes defining `__eq__` without `__hash__`).
- **Equal keys merge.** `1`, `1.0`, and `True` are one key; a `dict` keeps the first key object and the last value.
- **Integer hashing is not randomized.** On 64-bit CPython, `hash(n)` is `n` mod 2⁶¹ − 1 (and `hash(-1) == hash(-2)`), so chosen integer keys collide, making `dict`, `set`, and `Counter` quadratic. String and bytes hashes are keyed per process unless `PYTHONHASHSEED` is set.
- **Sorts are stable, heaps are not.** `heapq` ties compare the next tuple element, so `(priority, task)` raises `TypeError` for incomparable tasks; use `(priority, counter, task)`. `max`/`min` return the first extreme, `sorted(...)[-1]` the last. `sorted(x, reverse=True)` keeps equal elements in order; `sorted(x)[::-1]` reverses them.
- **`defaultdict` inserts on read,** changing `in`, `len`, and iteration.
- **Laziness.** `map`, `filter`, `zip`, and generators are single-use: a second pass silently sees nothing, `len` and indexing fail, and side effects and exceptions move to consumption. `zip` truncates silently (`strict=True` since 3.10).
- **Floating point.** Since 3.12, `sum()` of floats is compensated, so it can differ from a `+=` loop; `math.fsum` rounds exactly. `round` rounds half to even.
- **Floor division and modulo:** `-7 // 2 == -4`, `-7 % 2 == 1`.
- **Negative indices wrap:** `table[i - offset]` with `i` below the offset reads from the end instead of failing.
- **Huge integers.** Closed forms can create intermediates slower than the loop they replace. Converting an integer of more than 4300 digits to or from `str` raises `ValueError` (3.11+ and recent patch releases of older versions).
- **Exception types:** `list.index` raises `ValueError`, `d[k]` `KeyError`, `next(it)` `StopIteration`.
- **Aliasing:** `[[0] * n] * m` repeats one inner list; `list.sort()` returns `None`; mutable default arguments are shared.
- **`lru_cache` on a method** keeps every `self` alive and shares the cache across instances; arguments must be hashable; cached mutable results can be mutated by callers.

## Testing, profiling, and benchmarking

- **Tests:** pytest, `unittest`, doctest. pytest imports every `conftest.py` and auto-loads installed plugins; `pip install` (including `-e .`) runs `setup.py` and build backends; `tox.ini` and `noxfile.py` run arbitrary commands.
- **Testing an extracted function:** a module-level function with a leading underscore, imported by the test.
- **Property-based testing, if already present:** Hypothesis, including stateful testing (`RuleBasedStateMachine`); otherwise a seeded `random.Random(seed)`.
- **Profiling:** `cProfile` (deterministic, inflates call-heavy code); py-spy (sampling, attaches to a process) or Scalene if installed; `tracemalloc` for allocations and peak memory.
- **Benchmarks:** `timeit` for snippets; pyperf or pytest-benchmark if present. Account for garbage-collection pauses when the original runs with collection enabled.
- **Verification beyond tests** ("Verification levels" in `DIFFERENTIAL-TESTING.md`): CrossHair (symbolic execution; `crosshair diffbehavior` searches for inputs where two functions differ, within its bounds); Nagini. Type checkers prove types, not equivalence.
- **Constant-time comparison:** `hmac.compare_digest` (or `secrets.compare_digest`) for tokens and digests, not `==`.

## References

Sources: `references/languages/PYTHON.md`.
