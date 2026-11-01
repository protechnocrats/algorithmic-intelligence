# Kotlin

Load this file for Kotlin projects. First determine the target, which decides what exists and what it costs:

- **Kotlin/JVM** (server, desktop, tooling) and **Android**: the full Java standard library is available. `JAVA.md` documents it; consult it only for structures Kotlin lacks. For Android, also load `ANDROID.md`.
- **Multiplatform common code**: only `kotlin.collections`. No sorted map or set, priority queue, bitset, or `java.util.*`. Options: `expect`/`actual` wrappers over platform types, a small in-project implementation with tests, or a dependency (ask first, rule 7).
- **Kotlin/Native, JS, or Wasm**: `kotlin.collections` has its own implementations, without the JVM's treeified hash buckets. On Kotlin/JS, `Long` may be emulated in software; check before using it in a hot loop.

## Kotlin first (rule 14)

When Kotlin provides an equivalent, use the Kotlin structure or factory, not the Java class:

| Need | Use (Kotlin) | Instead of (Java) |
|---|---|---|
| Queue, stack, deque | `ArrayDeque` (`kotlin.collections`) | `java.util.ArrayDeque`, `LinkedList`, `Stack` |
| Dynamic list | `mutableListOf()`, `buildList { }`, `ArrayList` from `kotlin.collections` | `java.util.ArrayList()` imported from `java.util` |
| Hash map / set | `hashMapOf()`, `hashSetOf()`, `toHashSet()` | `java.util.HashMap()`, `java.util.HashSet()` |
| Insertion-ordered map / set | `mutableMapOf()`, `linkedMapOf()`, `mutableSetOf()`, `buildMap { }` | `java.util.LinkedHashMap()`, `java.util.LinkedHashSet()` |
| Sorted map / set | `sortedMapOf()`, `sortedSetOf()`, `toSortedMap()` | `java.util.TreeMap()`, `java.util.TreeSet()` |
| Sorting and searching | `sort()`, `sortBy { }`, `sortedWith()`, `binarySearch()`, `IntArray.sort()` | `Collections.sort`, `Arrays.sort`, `Collections.binarySearch` |
| String building | `buildString { }`, `joinToString()` | `StringBuilder` used directly (fine inside `buildString`) |

Use Java classes only when Kotlin has no equivalent, and state this in the report: `PriorityQueue`, `BitSet`, `EnumSet`, `EnumMap`, `java.util.concurrent` collections, `LinkedHashMap` with access order and `removeEldestEntry` (a bounded LRU cache), and `TreeMap`/`TreeSet` navigation (`floorKey`, `ceilingKey`, `headMap`, `pollFirst`): `sortedMapOf` is typed as `SortedMap`, which lacks these, so declare a `TreeMap` or `NavigableMap` when navigation is needed.

Only new code follows this preference; do not swap existing Java structures, since behavior can differ (`java.util.ArrayDeque` throws on `null`; Kotlin's `ArrayDeque` accepts it).

## Built-in structures

| Structure | Kotlin API | Key costs | Notes |
|---|---|---|---|
| Dynamic array | `mutableListOf`, `ArrayList` | get/set O(1), append amortized O(1), insert/remove at front O(n), `contains` O(n) | `listOf` is read-only, not immutable |
| Hash set / map | `hashSetOf`, `hashMapOf` | O(1) expected; on the JVM, O(log n) worst case per bucket only for `Comparable` keys | No order guarantee |
| Insertion-ordered set / map | `mutableSetOf`, `setOf`, `mutableMapOf`, `mapOf`, `toSet()`, `associate*`, `groupBy` | O(1) expected | **These all return `LinkedHashSet`/`LinkedHashMap`** |
| Double-ended queue | `kotlin.collections.ArrayDeque` | both ends O(1) amortized, indexed get O(1) | Common code; use for queues and BFS |
| Sorted set / map | `sortedSetOf`, `sortedMapOf` | O(log n) | JVM only |
| Priority queue | `java.util.PriorityQueue` | offer/poll O(log n), peek O(1), `remove(x)` O(n) | JVM only |
| Primitive arrays | `IntArray`, `LongArray`, `BooleanArray`, `DoubleArray` | O(1), no boxing | Prefer over `List<Int>` in hot numeric code (see the data-class trap) |
| Bitset, enum set / map | `java.util.BitSet`, `EnumSet`, `EnumMap` | O(1) per bit, O(n/64) bulk | JVM only |
| Lazy pipeline | `asSequence()` | No intermediate lists | Changes evaluation order (traps); can be slower on small inputs |
| Persistent collections | `kotlinx.collections.immutable` | Near-constant `add` with structural sharing | A dependency: ask. Replaces copy-on-every-update state (`state = state + item`) |

## Hidden costs

| Pattern | Cost | Fix |
|---|---|---|
| `list = list + item` or `+=` on a `var` of read-only `List` in a loop | Copies each step: O(n²) | `mutableListOf` and `add`, `buildList { }`, or a persistent list for shared state |
| `item in list`, `indexOf`, `first { }`, `find` inside a loop | O(n) per call | `toHashSet()` or `associateBy { }` once (traps: last duplicate wins, exception type) |
| `list - other`, `removeAll(other)`, `retainAll(other)` where `other` is a `List` | Linear search per element on current Kotlin versions: O(n·m) | Pass a `Set` |
| `set.elementAt(i)`, `Iterable.last()`, `count()` on a non-`List` in a loop | O(n) per call | Index a list, or keep the value |
| `list.removeAt(0)` as a queue; `remove` inside an index loop | O(n) per removal, O(n²) total | `ArrayDeque.removeFirst()`; `removeAll { }` or `retainAll { }`, which filter in place in O(n) |
| `windowed(k)` then aggregating each window | Allocates n lists of k: O(n·k) | Sliding aggregate in one loop: O(n) |
| `sorted()`, `sortedBy`, `maxBy` inside a loop | O(n log n) or O(n) per iteration | Sort once, or keep a `TreeMap` or heap |
| `groupBy { }.mapValues { it.value.size }` | Builds every group's list | `groupingBy { }.eachCount()` |
| `containsKey(k)` then `get(k)` or `put` | Two lookups | `getOrPut`, or `get` with a null check when `null` values are not meaningful |
| A sequence consumed by two terminal operations | Re-runs the whole chain each time | Materialize once with `toList()` |
| `filter { }.size`, `map { }.sum()` | Allocates a list | `count { }`, `sumOf { }` |
| `Pair(a, b)` or a `data class` as a hash key in hot code | Allocation and boxing per lookup; data classes do not cache `hashCode`, so a key holding a large list rehashes it on every lookup | Pack two `Int`s into a `Long`, or precompute a key |
| `List<Int>`, `Map<Int, Int>`, a `value class` in a generic or nullable position | Boxing, GC pressure, poor locality | `IntArray`, counting arrays, bitsets |
| `foo(*array)` in a loop | Spread copies the array | Pass the array |
| `string += x` in a loop; `Regex(...)` or `toRegex()` in a hot function | O(n²) copying; recompilation | `buildString { }`; hoist the `Regex` to a top-level or companion `val` |

## Coroutines and server-side Kotlin

- **N+1 queries.** Lazy JPA/Hibernate associations (`JOIN FETCH`, `@EntityGraph`) or Exposed DAO references (`.with(...)`) read in a loop issue one query per item.
- **Blocking inside coroutines.** JDBC, file I/O, or `Thread.sleep` on `Dispatchers.Default` or a request dispatcher starves its threads; `runBlocking` inside a coroutine can deadlock. Moving the call to `Dispatchers.IO` changes threading (rule 11): ask.
- **Per-item context switches.** `withContext` inside a loop over small items: switch once around the loop.
- **Sequential `await` in a loop → `awaitAll`.** Changes ordering of side effects, error behavior (the first failure cancels the scope), and load on the callee. Unbounded `async` per item can overwhelm a service; bound it with `Semaphore`, `limitedParallelism`, or `flatMapMerge(concurrency)`. Always a behavior change for review.
- **Flow operators.** `conflate` and `collectLatest` drop values; `buffer` changes producer-consumer interleaving. Adding them needs approval.

## Bit manipulation

| Operation | Kotlin |
|---|---|
| And, or, xor, not | `a and b`, `a or b`, `a xor b`, `a.inv()` |
| Shift left, arithmetic right, logical right | `a shl n`, `a shr n`, `a ushr n` |
| Popcount, trailing / leading zeros | `x.countOneBits()`, `x.countTrailingZeroBits()`, `x.countLeadingZeroBits()` |
| Lowest / highest set bit | `x.takeLowestOneBit()`, `x.takeHighestOneBit()` |
| 64 flags | `Long` with `1L shl i` (`1 shl i` is an `Int` and wraps at 32) |

Shifts use only the low 5 bits (`Int`) or 6 bits (`Long`) of the count, so `1 shl 32 == 1`. `%` is the remainder (sign of the dividend); `mod()` is the floor modulus. On the JVM, `EnumSet` is usually clearer than a raw enum mask.

## Kotlin-specific traps

- **Ordered by default.** `mutableSetOf`, `mutableMapOf`, `toSet`, `associateBy`, and `groupBy` preserve insertion order; switching to `HashSet`/`HashMap` changes iteration order.
- **Duplicates:** `associateBy` and `toMap` keep the last value for a key; a `first { }` search returned the first.
- **Exception types.** `first { }` throws `NoSuchElementException`; `map[k]!!` throws `NullPointerException`; `getValue(k)` throws `NoSuchElementException` with a different message. Replacing a search with a lookup must keep the original's exception, or it is a behavior change.
- **Floating-point equality depends on the static type.** `a == b` on values typed `Double` or `Float` follows IEEE 754 (`NaN != NaN`, `-0.0 == 0.0`). Inside collections, generics, and `Any`, equality uses `equals`: `NaN` equals itself and `-0.0 != 0.0`. Moving a `==` loop over doubles into a `Set`, `Map`, or `contains` changes results for `NaN` and `-0.0`. `sorted()` on doubles puts `NaN` last; `maxOrNull()` returns `NaN` if any value is `NaN`; a manual `>` loop skips it.
- **Data classes with array properties** compare arrays by reference in `equals` and `hashCode`. Replacing a `List<Int>` property with `IntArray` silently changes equality, hashing, and `toString`.
- **Mutable keys.** A `data class` with `var` properties used as a hash key breaks when mutated.
- **Stable sorts.** `sort`, `sortBy`, `sortedWith`, and `Array<T>.sortWith` are stable on every target. `binarySearch` may return any index among equal elements.
- **`maxBy`/`maxOf` return the first maximal element;** `sortedBy { }.last()` returns the last one.
- **Sequences are lazy.** They interleave `map` and `filter` lambdas element by element and run nothing until a terminal operation, changing the order and number of lambda calls.
- **`split` differs from Java's.** Kotlin's `split(",")` is literal and keeps trailing empty strings; Java's `String.split` takes a regex and drops them.
- **Silent `Int` overflow.** A closed form can overflow where the loop did not; `sum()` on `List<Int>` wraps. Use `Long`, `sumOf { it.toLong() }`, or `Math.multiplyExact`.
- **Non-atomic `getOrPut`.** On a `ConcurrentHashMap` it can run the default more than once; use `computeIfAbsent` when that matters.
- **Read-only is not immutable.** An internal `MutableList` returned as `List` can be mutated by Java callers.

## Testing, profiling, and benchmarking

- **Tests:** JUnit 4 or 5, `kotlin.test`, Kotest; `kotlinx-coroutines-test` (`runTest`, virtual time); Turbine for Flow.
- **Property-based testing, if already present:** Kotest property testing (`kotest-property`), jqwik.
- **Profiling:** on the JVM, async-profiler (CPU, allocation, and lock profiles as flame graphs) or Java Flight Recorder (`-XX:StartFlightRecording`); IntelliJ's profiler wraps both. Kotlin/Native: `perf` or Instruments.
- **Benchmarks, if already present:** kotlinx-benchmark or JMH (`-prof gc` reports allocation per operation). Otherwise a timing harness with `System.nanoTime()`, warmup iterations, and medians; JIT warmup and dead-code elimination distort naive timings.
- **Verification beyond tests** (see "Verification levels" in `DIFFERENTIAL-TESTING.md`; ask unless present): Lincheck checks concurrent structures for linearizability, with a model-checking mode that enumerates interleavings; on JVM targets, jcstress and JBMC from `JAVA.md` also apply.
- **Constant-time comparison** (for secrets; see `techniques/hostile-inputs.md`): on the JVM, `java.security.MessageDigest.isEqual`, never `contentEquals` or `==`.

## References (for verifying claims; not required reading)

- Kotlin collections: kotlinlang.org/docs/collections-overview.html; API reference: kotlinlang.org/api/core/kotlin-stdlib/
- Floating-point comparison: kotlinlang.org/docs/numbers.html#floating-point-numbers-comparison
- Coroutines: kotlinlang.org/docs/coroutines-guide.html
