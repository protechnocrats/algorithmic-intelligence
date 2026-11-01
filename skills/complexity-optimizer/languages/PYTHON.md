# Python

Load this file for Python projects. Record the interpreter and version (`requires-python`, `.python-version`, CI matrix): CPython is the default, but PyPy's JIT, GraalPy, and the free-threaded CPython builds (3.13+, no global interpreter lock) change which costs matter. Several APIs below are version-specific.

## Built-in structures

| Structure | API | Key costs | Notes |
|---|---|---|---|
| Dynamic array | `list` | index O(1), `append`/`pop()` amortized O(1), **`insert(0, x)`/`pop(0)` O(n)**, `in`/`index`/`remove`/`count` O(n), slice copy O(k) | |
| Hash map | `dict` | O(1) expected | **Insertion order is guaranteed** (3.7+) |
| Hash set | `set`, `frozenset` | O(1) expected | **No order guarantee**; string iteration order changes per process |
| Counting, grouping | `collections.Counter`, `defaultdict` | O(1) expected per update | `Counter.most_common(k)` is O(n log k) |
| Double-ended queue | `collections.deque` | both ends O(1); **indexing toward the middle O(n)** | `maxlen` gives a bounded ring buffer |
| Ordered map with reordering | `collections.OrderedDict` | `move_to_end`, `popitem(last=False)` O(1) | A bounded LRU cache without a dependency |
| Priority queue | `heapq` on a `list` | push/pop O(log n), `heapify` O(n), `nsmallest(k)` O(n log k) | **Min-heap**, not stable; no decrease-key |
| Sorted sequence | `bisect` on a `list` | search O(log n), **`insort` O(n)** | `key=` since 3.10. No balanced tree in the standard library |
| Compact typed arrays | `array.array`, `bytearray`, `memoryview` | O(1) access, no per-element objects | `memoryview` slices without copying |
| Arbitrary-size bitset | `int` | `&`, `\|`, `^` O(n/30) | Immutable: setting one bit copies the whole integer |
| Caching | `functools.lru_cache(maxsize=...)`, `functools.cache` (3.9+) | O(1) expected | **`cache` and `lru_cache(maxsize=None)` are unbounded** (rule 1) |
| Topological order | `graphlib.TopologicalSorter` (3.9+) | O(V + E) | |
| Iterator tools | `itertools` (`accumulate`, `groupby`, `islice`, `pairwise` 3.10+, `batched` 3.12+), `heapq.merge` | Lazy, O(1) memory | `groupby` groups only consecutive equal keys |

**Not in the standard library:** sorted containers with O(log n) insertion (`sortedcontainers`), tries, interval trees, compact bitsets with fast single-bit updates (`bitarray`), and vectorized numeric arrays (NumPy). Each is a dependency: ask first (rule 7). Compiling hot code (Cython, mypyc, Numba, a Rust or C extension) is a build change: ask.

## Hidden costs

| Pattern | Cost | Fix |
|---|---|---|
| `x in items` on a list or `dict.values()` inside a loop | O(n) per check | A `set` or `dict` built once (traps: hashability, order) |
| `if x in set(items)` inside a loop | Rebuilds the set each time: still O(n) per check | Build the set outside the loop |
| `queue.pop(0)` or `insert(0, x)` | O(n) per call | `collections.deque` |
| `result = result + [x]`, `sum(list_of_lists, [])`, `bytes +=` in a loop | O(n²) copying | `append`, `itertools.chain.from_iterable`, `bytearray` or `b"".join` |
| `s += piece` for strings in a loop | CPython often reuses the buffer, but not guaranteed and quadratic on PyPy | `"".join(pieces)` or `io.StringIO` |
| `s[i:]` or `lst[1:]` in a loop or recursion | Each slice copies: O(n²) total | Pass indices; `memoryview` for bytes |
| `bisect.insort` to keep a growing list sorted | O(n) per insert, O(n²) total | `heapq` if only the minimum is needed; sort once at the end; `sortedcontainers` (ask) |
| `sorted(...)`, `min`, or `max` over a whole collection inside a loop | O(n log n) or O(n) per iteration | Sort once, keep a heap, or carry the running answer |
| `statistics.mean`, `median` on large float data | Exact `Fraction` arithmetic, much slower | `statistics.fmean` (3.8+) or `sum/len`, which can change the last digits: a behavior change |
| `copy.deepcopy` in a loop | Walks the whole object graph | Copy only what changes, or share immutable parts |
| Deep recursion (DFS, recursive descent, memoized recursion) | `RecursionError` near 1000 frames, and per-call overhead | An explicit stack; raising the recursion limit can crash the interpreter on the C stack. A `RecursionError` on accepted input is a bug (rule 4) |
| CPU-bound threads on a build with the global interpreter lock | No parallel speedup | Processes (pickling and side-effect order change), vectorization, or a free-threaded build; all need approval |
| Global and attribute lookups, small function calls in tight loops | Constant factor only | Change only with a measurement; leave idiomatic code alone otherwise (rule 13) |

## asyncio

A blocking call (`time.sleep`, synchronous network, file, or database calls, heavy CPU work) inside a coroutine stalls the whole event loop. `await` in a loop over independent items → `asyncio.gather` or a `TaskGroup` (3.11+) changes ordering, error behavior (cancellation of siblings), and load on the callee: a behavior change for review, bounded with a `Semaphore`.

## Bit manipulation

| Operation | Python |
|---|---|
| And, or, xor, not, shifts | `&`, `\|`, `^`, `~` (`~x == -x - 1`), `<<`, `>>` (arithmetic; no logical shift) |
| Popcount | `x.bit_count()` (3.10+), else `bin(x).count("1")` |
| Highest bit, lowest set bit | `x.bit_length()`, `x & -x` |
| Fixed-width behavior | Integers never overflow: emulate 32- or 64-bit wraparound with `& 0xFFFFFFFF` and sign conversion |

Python integers are arbitrary precision, so a bitmask holds any number of flags, but every operation costs time proportional to the integer's size and creates a new object. For many single-bit updates on a large set, a `bytearray` (one byte per flag) is faster.

## Python-specific traps

- **Order.** `dict` keeps insertion order; `set` does not. Deduplicating a list through `set` loses order; `list(dict.fromkeys(items))` keeps the first occurrence in order.
- **Hashability.** Replacing `in list` with a `set` raises `TypeError` for unhashable elements (lists, dicts, plain dataclasses with `eq=True` and not `frozen`, any class that defines `__eq__` without `__hash__`). Linear search accepted them.
- **Equal keys merge.** `1`, `1.0`, and `True` are one key; a `set` or `dict` keeps the first key object inserted and the last value.
- **Integer hashing is not randomized.** On 64-bit CPython, `hash(n)` is `n` modulo 2⁶¹ − 1 (and `hash(-1) == hash(-2)`), so integer keys an attacker chooses can all collide, making `dict`, `set`, and `Counter` quadratic. String and bytes hashes are keyed per process (unless `PYTHONHASHSEED` is set). See `techniques/hostile-inputs.md`.
- **Stable sorts, unstable heaps.** `sorted` and `list.sort` are guaranteed stable. `heapq` is not, and ties compare the next tuple element: `(priority, task)` raises `TypeError` when tasks are not comparable. Use `(priority, counter, task)`. `max` and `min` return the first maximal element; `sorted(...)[-1]` returns the last.
- **Laziness.** `map`, `filter`, `zip`, and generators are single-use iterators: converting a list to a generator breaks a second pass, `len`, and indexing, and moves side effects and exceptions to the point of consumption. `zip` silently truncates (`strict=True` since 3.10).
- **Floating point.** Since 3.12, `sum()` of floats uses compensated summation, so it can differ from an explicit `+=` loop; `math.fsum` is exact rounding. Reordering a sum changes results. `round` rounds half to even.
- **Integer division and modulo floor:** `-7 // 2 == -4` and `-7 % 2 == 1`, unlike C and Java.
- **Negative indices wrap.** `table[i - offset]` with `i` below the offset returns an element from the end instead of failing. A table lookup that replaces a computation must keep the original's range checks and exceptions.
- **Huge integers.** Closed forms can create huge intermediates whose arithmetic is slower than the loop they replace. Converting an integer of more than 4300 digits to or from `str` raises `ValueError` (3.11+, and recent patch releases of older versions).
- **Exception types.** `list.index` raises `ValueError`, `d[k]` raises `KeyError`, `next(it)` raises `StopIteration`. A rewrite must raise the same type in the same cases, or return `None` exactly where the original did.
- **Aliasing and mutation.** `[[0] * n] * m` repeats one inner list; `list.sort()` mutates and returns `None`; a mutable default argument is shared between calls.
- **Caching.** `lru_cache` on a method keeps every `self` alive and shares the cache across instances; arguments must be hashable; cached mutable return values can be mutated by callers.

## Testing, profiling, and benchmarking

- **Tests:** pytest, `unittest`, doctest.
- **Property-based testing, if already present:** Hypothesis, including stateful testing (`RuleBasedStateMachine`) against a simple model. Otherwise a seeded `random.Random(seed)` generator.
- **Profiling:** `cProfile` with `pstats` (standard library, deterministic, inflates call-heavy code); py-spy (sampling, attaches to a running process, no code changes) or Scalene (CPU, memory, and native time per line) if installed; `tracemalloc` (standard library) for allocations and peak memory.
- **Benchmarks:** `timeit` (standard library) for small snippets; pyperf or pytest-benchmark if present, which calibrate loops and report variance. Disable or account for garbage collection pauses only when the original runs with GC enabled.
- **Verification beyond tests** (see "Verification levels" in `DIFFERENTIAL-TESTING.md`; installs, so ask unless present): CrossHair checks contracts by symbolic execution with an SMT solver, and `crosshair diffbehavior` searches for inputs where two functions differ, which is an equivalence check within its search bounds; Nagini verifies annotated programs with a prover. Type checkers (mypy, pyright) prove type facts only, never equivalence.
- **Constant-time comparison** (for secrets; see `techniques/hostile-inputs.md`): `hmac.compare_digest` (also `secrets.compare_digest`), never `==` on tokens or digests.

## References (for verifying claims; not required reading)

- Operation costs of built-in types: wiki.python.org/moin/TimeComplexity; standard library: docs.python.org/3/library/
- Hashing of numeric types: docs.python.org/3/library/stdtypes.html#hashing-of-numeric-types
- Integer string conversion limit: docs.python.org/3/library/stdtypes.html#int-max-str-digits
