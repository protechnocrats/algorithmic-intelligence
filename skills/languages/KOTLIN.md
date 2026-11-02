# Kotlin

Load this file for Kotlin projects. First determine the target, which decides what exists and what it costs:

- **Kotlin/JVM**: the full Java standard library is available. `JAVA.md` documents it; consult it only for structures Kotlin lacks.
- **Multiplatform common code**: only `kotlin.collections`. No sorted map or set, priority queue, bitset, or `java.util.*`. Options: `expect`/`actual` wrappers over platform types, a small in-project implementation with tests, or a dependency (ask first, rule 7).
- **Kotlin/Native, JS, or Wasm**: `kotlin.collections` has its own implementations; do not assume JVM behavior. On Kotlin/JS, `Long` is a `BigInt` only on ES2020 targets or with an experimental flag; check before using it in a hot loop. A Kotlin collection passed to Swift is copied in full, so crossing that boundary in a loop is O(n) per crossing.

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

Only new code follows this preference; do not swap existing Java structures, since behavior can differ (`java.util.ArrayDeque` throws on `null`; Kotlin's `ArrayDeque` accepts it, measured on Kotlin 2.4).

## Built-in structures

| Structure | Kotlin API | Key costs | Notes |
|---|---|---|---|
| Dynamic array | `mutableListOf`, `ArrayList` | get/set O(1), append amortized O(1), insert/remove at front O(n), `contains` O(n) | `listOf` is read-only, not immutable |
| Hash set / map | `hashSetOf`, `hashMapOf` | O(1) expected; worst case under "Unkeyed hashing" | No order guarantee |
| Insertion-ordered set / map | `mutableSetOf`, `setOf`, `mutableMapOf`, `mapOf`, `toSet()`, `associate*`, `groupBy` | O(1) expected | **All preserve insertion order** |
| Double-ended queue | `kotlin.collections.ArrayDeque` | both ends O(1) amortized, indexed get O(1) | Common code; use for queues and BFS |
| Sorted set / map | `sortedSetOf`, `sortedMapOf` | O(log n) | JVM only |
| Priority queue | `java.util.PriorityQueue` | offer/poll O(log n), peek O(1), `remove(x)` O(n) | JVM only |
| Primitive arrays | `IntArray`, `LongArray`, `BooleanArray`, `DoubleArray` | O(1), no boxing | Prefer over `List<Int>` in hot code (see the array-equality trap) |
| Bitset, enum set / map | `java.util.BitSet`, `EnumSet`, `EnumMap` | O(1) per bit, O(n/64) bulk | JVM only |
| Lazy pipeline | `asSequence()` | No intermediate lists | Changes evaluation order (traps); can be slower than lists on small inputs, so measure |
| Persistent collections | `kotlinx.collections.immutable` | Updates share storage with the original instead of copying it | An experimental, pre-1.0 dependency: ask. Replaces copy-on-every-update state (`state = state + item`) |

## Hidden costs

This table lists common traps, not every operation. Every call counts at its real cost, including ones not listed here ("Count every call at its real cost" under rule 6 in `SKILL.md`).

| Pattern | Cost | Fix |
|---|---|---|
| `list = list + item` or `+=` on a `var` of read-only `List` in a loop | Copies each step: O(n²) | `mutableListOf` and `add`, `buildList { }`, or a persistent list |
| `item in list`, `indexOf`, `first { }`, `find` inside a loop | O(n) per call | `toHashSet()` or `associateBy { }` once (traps: duplicates, exception type, floating-point equality) |
| `list - other`, `removeAll(other)`, `retainAll(other)` where `other` is a `List` | Linear search per element: O(n·m) (measured on Kotlin 2.4; the docs state no cost) | Pass a `Set` |
| `set.elementAt(i)`, `Iterable.last()`, `count()` on a non-`List` in a loop | O(n) per call | Index a list, or keep the value |
| `list.removeAt(0)` as a queue; `remove` inside an index loop | O(n) per removal, O(n²) total | `ArrayDeque.removeFirst()`; `removeAll { }` or `retainAll { }`, which filter in place in O(n) (measured on Kotlin 2.4; the docs state no cost) |
| `windowed(k)` then aggregating each window | Allocates n lists of k: O(n·k) | Sliding aggregate in one loop: O(n) |
| `sorted()`, `sortedBy`, `maxBy` inside a loop | O(n log n) or O(n) per iteration | Sort once, or keep a `TreeMap` or heap |
| `groupBy { }.mapValues { it.value.size }` | Builds every group's list | `groupingBy { }.eachCount()` |
| `containsKey(k)` then `get(k)` | Two lookups | `get` with a null check, or `getOrPut` (trap: `null` values) |
| A sequence consumed by two terminal operations | Re-runs the whole chain each time | Materialize once with `toList()` |
| `filter { }.size`, `filter { }.isNotEmpty()`, `map { }.sum()` | Builds a whole intermediate list | `count { }`, `any { }`, `sumOf { }` |
| `Pair(a, b)` or a `data class` as a hash key in hot code | Allocation and boxing per lookup; a data class's generated `hashCode` recomputes over every property on each call, so a key holding a large list rehashes it every lookup | Index an `IntArray` (`r * width + c`) when keys are dense; pack two `Int`s into one `Long` (still boxed as a key, but one object instead of three) |
| `List<Int>`, `Map<Int, Int>`, a `value class` in a generic or nullable position | Boxing, GC pressure, poor locality | `IntArray`, counting arrays, bitsets |
| `foo(*array)` in a loop | The compiler copies the array: O(n) per call, and the callee's writes do not reach the caller's array (undocumented; measured on Kotlin 2.4) | Pass the array, if measured to matter; a rewrite that passes it directly lets the callee change the caller's data, which is a behavior change |
| `string += x` in a loop; `Regex(...)` or `toRegex()` in a hot function | O(n²) copying; recompilation | `buildString { }`; hoist the `Regex` to a top-level or companion `val` |

## Bit manipulation

| Operation | Kotlin |
|---|---|
| And, or, xor, not | `a and b`, `a or b`, `a xor b`, `a.inv()` |
| Shift left, arithmetic right, logical right | `a shl n`, `a shr n`, `a ushr n` |
| Popcount, trailing / leading zeros | `x.countOneBits()`, `x.countTrailingZeroBits()`, `x.countLeadingZeroBits()` |
| Lowest / highest set bit | `x.takeLowestOneBit()`, `x.takeHighestOneBit()` |
| 64 flags | `Long` with `1L shl i` (`1 shl i` is an `Int` and wraps at 32) |

Shifts use only the low 5 bits (`Int`) or 6 bits (`Long`) of the count, so `1 shl 32 == 1` and `1L shl 64 == 1L` (confirmed on Kotlin 2.4). `%` is the remainder (sign of the dividend); `mod()` is the floor modulus. On the JVM, `EnumSet` is usually clearer than a raw enum mask.

## Kotlin-specific traps

- **Ordered by default.** The insertion-ordered row above; switching to `HashSet`/`HashMap` changes iteration order.
- **Duplicates:** `associateBy` and `toMap` keep the last value for a key; a `first { }` search returned the first.
- **Exception types.** `first { }` throws `NoSuchElementException`; `map[k]!!` throws `NullPointerException`; `getValue(k)` throws `NoSuchElementException` with a different message. Replacing a search with a lookup must keep the original's exception.
- **`getOrPut` treats a `null` value as missing** and replaces it; `containsKey` does not. Kotlin 2.4 adds explicit `getOrPutIfMissing` and `getOrPutIfNull` (experimental). On a `ConcurrentMap`, `getOrPut` may run the default even when the key is present; use `computeIfAbsent` when that matters.
- **Floating-point equality depends on the static type.** `a == b` on values typed `Double` or `Float` follows IEEE 754 (`NaN != NaN`, `-0.0 == 0.0`). In collections, generics, and `Any`, it uses `equals`: `NaN` equals itself and `-0.0 != 0.0`. Moving a `==` loop into a `Set`, `Map`, or `contains` changes results for `NaN` and `-0.0`. A data class's generated `equals` compares `Double` properties with the `equals` rule, not IEEE 754: `Point(NaN) == Point(NaN)` is `true` and `Point(0.0) == Point(-0.0)` is `false` (undocumented; measured on Kotlin 2.4). Replacing a field-by-field `==` comparison with data-class equality, or the reverse, changes results for `NaN` and `-0.0`. `sorted()` puts `NaN` last; `maxOrNull()` returns `NaN` if any value is `NaN`; a manual `>` loop skips it.
- **Arrays compare by reference** in `==`, sets, maps, `distinct()`, and data-class `equals`/`hashCode`. Replacing a `List<Int>` with `IntArray` silently changes all of them; `contentEquals` and `contentHashCode` compare contents.
- **Mutable keys.** A `data class` with `var` properties used as a hash key breaks when mutated: the entry can no longer be found. `==` calls `equals`; `===` compares references.
- **Unkeyed hashing.** On the JVM, `String.hashCode` and integer hashes are fixed functions, so an attacker can choose colliding keys. `HashMap` "may use comparison order" to break ties only for `Comparable` keys (OpenJDK: O(log n) per bucket); data-class keys, and the Native and JS implementations, get no such help. Treat the worst case as O(n) per lookup. See `techniques/hostile-inputs.md`.
- **Stable sorts.** `sort`, `sortBy`, `sortedWith`, and `Array<T>.sortWith` are stable on every target. `sortedBy { }.reversed()` reverses equal elements; `sortedByDescending { }` keeps their order. `binarySearch` may return any index among equal elements.
- **`maxBy`, `maxWith`, `minBy` return the first extreme element;** `sortedBy { }.last()` returns the last.
- **Sequences are lazy.** They interleave `map` and `filter` lambdas element by element and run nothing until a terminal operation, changing the order and number of lambda calls.
- **Strings are UTF-16.** `length` counts code units; `reversed()` splits surrogate pairs. `split(",")` is literal and keeps trailing empty strings; Java's `String.split` takes a regex and drops them.
- **Silent `Int` overflow.** A closed form can overflow where the loop did not; `sum()` on `List<Int>` wraps. Use `Long`, `sumOf { it.toLong() }`, or `Math.multiplyExact`.
- **Concurrency.** Making sequential suspending calls concurrent changes the order of side effects, error propagation, cancellation, and load on the callee: a behavior change for review.
- **Read-only is not immutable.** An internal `MutableList` returned as `List` can be mutated by Java callers.

## Testing, profiling, and benchmarking

- **Tests:** JUnit 4 or 5, `kotlin.test`, Kotest.
- **Property-based testing, if already present:** Kotest property testing (`kotest-property`), whose `Exhaustive` generators enumerate whole small domains (level 3); jqwik.
- **Profiling:** on the JVM, async-profiler (CPU, allocation, and lock flame graphs) or Java Flight Recorder (`-XX:StartFlightRecording`). Kotlin/Native: `perf` or Instruments.
- **Benchmarks, if already present:** kotlinx-benchmark or JMH (`-prof gc` reports allocation per operation). Otherwise `System.nanoTime()` with warmup and medians; JIT warmup and dead-code elimination distort naive timings.
- **Verification beyond tests** (see "Verification levels" in `DIFFERENTIAL-TESTING.md`; ask unless present): Lincheck checks concurrent structures for linearizability, with a model-checking mode that enumerates interleavings; on JVM targets, jcstress and JBMC from `JAVA.md` also apply.
- **Constant-time comparison** (for secrets; see `techniques/hostile-inputs.md`): on the JVM, `java.security.MessageDigest.isEqual`, whose time depends only on the length of its first argument, so pass the expected value first; never `contentEquals` or `==`.

## References (for verifying claims; not required reading)

- Kotlin collections: kotlinlang.org/docs/collections-overview.html; API reference: kotlinlang.org/api/core/kotlin-stdlib/
- Floating-point comparison: kotlinlang.org/docs/numbers.html#floating-point-numbers-comparison
