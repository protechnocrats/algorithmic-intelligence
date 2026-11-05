# Kotlin

First determine the target, which decides what exists and what it costs:

- **Kotlin/JVM**: the Java standard library is available (`JAVA.md`), used only for structures Kotlin lacks.
- **Multiplatform common code**: only `kotlin.collections`; no sorted map or set, priority queue, bitset, or `java.util`. Options: `expect`/`actual` wrappers, a small in-project implementation with tests, or a dependency (rule 7).
- **Kotlin/Native, JS, Wasm**: `kotlin.collections` has its own implementations, so JVM costs and behavior do not carry over. On Kotlin/JS, `Long` is a `BigInt` only on ES2020 targets or with an experimental flag. A read-only Kotlin `List`, `Set`, or `Map` passed to Swift arrives as `NSArray`, `NSSet`, `NSDictionary` and bridges to Swift collections; whether each crossing copies (O(n)) or bridges lazily is `[unverified]`, so check the interop documentation for the project's version or measure. Mutable collections map to `NSMutableArray` and the like.

**Contents:** Kotlin first (rule 14) · Built-in structures · Hidden costs · Bit manipulation · Kotlin-specific traps · Testing, profiling, and benchmarking · References

Costs marked *(measured)* below are not in the official documentation; they were measured on Kotlin 2.4 and can change between versions.

## Kotlin first (rule 14)

For structures you introduce, use the Kotlin structure or factory when one exists:

| Need | Use (Kotlin) | Instead of (Java) |
|---|---|---|
| Queue, stack, deque | `ArrayDeque` (`kotlin.collections`) | `java.util.ArrayDeque`, `LinkedList`, `Stack` |
| Dynamic list | `mutableListOf()`, `buildList { }` | `java.util.ArrayList()` |
| Hash map / set | `hashMapOf()`, `hashSetOf()`, `toHashSet()` | `java.util.HashMap()`, `HashSet()` |
| Insertion-ordered map / set | `mutableMapOf()`, `linkedMapOf()`, `mutableSetOf()`, `buildMap { }` | `LinkedHashMap()`, `LinkedHashSet()` |
| Sorted map / set | `sortedMapOf()`, `sortedSetOf()`, `toSortedMap()` | `TreeMap()`, `TreeSet()` |
| Sorting and searching | `sort()`, `sortBy { }`, `sortedWith()`, `binarySearch()` | `Collections.sort`, `Arrays.sort`, `Collections.binarySearch` |
| String building | `buildString { }`, `joinToString()` | `StringBuilder` directly |

Java classes with no Kotlin equivalent: `PriorityQueue`, `BitSet`, `EnumSet`, `EnumMap`, `java.util.concurrent`, access-ordered `LinkedHashMap` with `removeEldestEntry` (a bounded LRU cache), and `TreeMap` navigation (`floorKey`, `ceilingKey`, `headMap`, `pollFirstEntry`): `sortedMapOf` is typed `SortedMap`, which lacks these, so declare a `TreeMap` or `NavigableMap`. `sortedSetOf` already returns a `java.util.TreeSet` with `floor`, `ceiling`, `pollFirst`.

Do not swap existing Java structures for this preference alone: behavior differs (`java.util.ArrayDeque` throws on `null`; Kotlin's accepts it *(measured)*).

## Built-in structures

| Structure | Kotlin API | Key costs | Notes |
|---|---|---|---|
| Dynamic array | `mutableListOf`, `ArrayList` | get/set O(1), append amortized O(1), front insert/remove O(n), `contains` O(n) | `listOf` is read-only, not immutable |
| Hash set / map | `hashSetOf`, `hashMapOf` | O(1) expected; worst case under "Unkeyed hashing" | No order guarantee |
| Insertion-ordered set / map | `mutableSetOf`, `setOf`, `mutableMapOf`, `mapOf`, `toSet()`, `associate*`, `groupBy` | O(1) expected | All preserve insertion order |
| Double-ended queue | `kotlin.collections.ArrayDeque` | both ends O(1) amortized, indexed get O(1) | Common code |
| Sorted set / map | `sortedSetOf`, `sortedMapOf` | O(log n) | JVM only |
| Priority queue | `java.util.PriorityQueue` | offer/poll O(log n), `remove(x)` O(n) | JVM only |
| Primitive arrays | `IntArray`, `LongArray`, `BooleanArray`, `DoubleArray` | O(1), no boxing | See the array-equality trap |
| Bitset, enum set / map | `java.util.BitSet`, `EnumSet`, `EnumMap` | O(1) per bit, O(n/64) bulk | JVM only |
| Lazy pipeline | `asSequence()` | No intermediate lists | Changes evaluation order; can be slower on small inputs |
| Persistent collections | `kotlinx.collections.immutable` | Updates share storage instead of copying | Experimental pre-1.0 dependency; replaces copy-per-update state (`state = state + item`) |

## Hidden costs

| Pattern | Cost | Fix |
|---|---|---|
| `list = list + item` or `+=` on a `var` read-only `List` in a loop | Copies each step: O(n²) | `mutableListOf` and `add`, `buildList { }`, or a persistent list |
| `item in list`, `indexOf`, `first { }`, `find` in a loop | O(n) per call | `toHashSet()` or `associateBy { }` once (traps: duplicates, exception type, float equality) |
| `list - other`, `removeAll(other)`, `retainAll(other)` with `other` a `List` | O(n·m) when `other` is a `listOf(...)` *(measured)*. `[unverified]`: the stdlib may convert an `ArrayList` of more than two elements to a `HashSet` first (`convertToSetForSetOperationWith`), giving O(n + m) and hash equality; check the source for the project's version or measure both | Pass a `Set` |
| `elementAt(i)` or `last()` on a non-`List`, `count()` on a `Sequence` or non-`Collection` `Iterable`, in a loop | O(n) per call (`count()` on any `Collection` is O(1); on a `Sequence` it re-runs the chain) | Index a list, or keep the value |
| `removeAt(0)` as a queue; `remove` inside an index loop | O(n) per removal | `ArrayDeque.removeFirst()`; `removeAll { }`/`retainAll { }` filter in place in O(n) *(measured)* |
| `windowed(k)` then aggregating each window | O(n·k) allocation | A sliding aggregate: O(n) |
| `sorted()`, `sortedBy`, `maxBy` inside a loop | O(n log n) or O(n) per iteration | Sort once, or a `TreeMap` or heap |
| `groupBy { }.mapValues { it.value.size }` | Builds every group's list | `groupingBy { }.eachCount()` |
| `containsKey(k)` then `get(k)` | Two lookups | `get` with a null check, or `getOrPut` (null-value trap) |
| A sequence consumed by two terminal operations | Re-runs the chain | `toList()` once |
| `filter { }.size`, `filter { }.isNotEmpty()`, `map { }.sum()` | An intermediate list | `count { }`, `any { }`, `sumOf { }` |
| `Pair(a, b)` or a `data class` as a hash key in hot code | Allocation and boxing per lookup; a data class's `hashCode` recomputes over every property each call, so a key holding a large list rehashes it every lookup | `IntArray` indexed `r * width + c` for dense keys; pack two `Int`s into one `Long` (one boxed object instead of three) |
| `List<Int>`, `Map<Int, Int>`, a `value class` in a generic or nullable position | Boxing, GC, poor locality | `IntArray`, counting arrays, bitsets |
| `foo(*array)` in a loop | Copies the array: O(n) per call, and the callee's writes do not reach the caller *(measured)* | Pass the array if it matters; then the callee can change the caller's data, a behavior change |
| `string += x` in a loop; `Regex(...)`/`toRegex()` in a hot function | O(n²) copying; recompilation | `buildString { }`; hoist the `Regex` to a top-level or companion `val` |

### Input handling and security

- **Number parsing.** `toInt()`, `toLong()`, and their `OrNull` forms accept non-ASCII digits (`"٥".toInt() == 5`) and a leading `+`, but no whitespace. On the JVM, `toDouble()` follows `Double.parseDouble` (`JAVA.md`); check other targets. `Char.isDigit()` is also true for non-ASCII digits.
- **Regex backtracks** on the JVM and JS. `Regex.escape` for input in a pattern, `Regex.escapeReplacement` for input in a replacement.
- **Locale and time zone.** `uppercase()`/`lowercase()` use the invariant locale; the deprecated `toUpperCase()`/`toLowerCase()` use the default (Turkish `ı`). `"%.2f".format(x)` and `String.format` use the default locale's separator; clock and date calls without a zone read the default zone. All are hidden inputs to a cache or precomputed table.
- **Recursion** throws `StackOverflowError` at a depth set by the thread's stack; `DeepRecursiveFunction` keeps the recursive shape on the heap. Java serialization of untrusted data is unsafe as in `JAVA.md`.

## Bit manipulation

| Operation | Kotlin |
|---|---|
| And, or, xor, not | `and`, `or`, `xor`, `inv()` |
| Shift left, arithmetic right, logical right | `shl`, `shr`, `ushr` |
| Popcount, trailing / leading zeros | `countOneBits()`, `countTrailingZeroBits()`, `countLeadingZeroBits()` |
| Lowest / highest set bit | `takeLowestOneBit()`, `takeHighestOneBit()` |
| 64 flags | `Long` with `1L shl i` (`1 shl i` is an `Int`) |

Shift counts use the low 5 (`Int`) or 6 (`Long`) bits: `1 shl 32 == 1`, `1L shl 64 == 1L`. `%` takes the dividend's sign; `mod()` is the floor modulus.

## Kotlin-specific traps

- **Ordered by default.** Switching the default sets and maps to `HashSet`/`HashMap` changes iteration order.
- **Duplicates:** `associateBy` and `toMap` keep the last value for a key; a `first { }` search returned the first.
- **Exception types.** `first { }` throws `NoSuchElementException`; `map[k]!!` throws `NullPointerException`; `getValue(k)` throws `NoSuchElementException` with a different message.
- **`getOrPut` treats a `null` value as missing** and replaces it. Kotlin 2.4 adds experimental `getOrPutIfMissing` and `getOrPutIfNull`. On a `ConcurrentMap`, `getOrPut` may run the default even when the key is present; use `computeIfAbsent` when that matters.
- **Floating-point equality depends on the static type.** `==` on values typed `Double`/`Float` is IEEE 754 (`NaN != NaN`, `-0.0 == 0.0`); in collections, generics, `Any`, and data-class `equals` it is `equals` (`NaN` equals itself, `-0.0 != 0.0`; the data-class case is undocumented *(measured)*). Moving a `==` loop into a `Set`, `Map`, `contains`, or data-class comparison changes results for `NaN` and `-0.0`. `sorted()` puts `NaN` last; `maxOrNull()` returns `NaN` if any value is `NaN`; a manual `>` loop skips it.
- **Arrays compare by reference** in `==`, sets, maps, `distinct()`, and data-class `equals`/`hashCode`; replacing `List<Int>` with `IntArray` changes all of them. `contentEquals`/`contentHashCode` compare contents.
- **Mutable keys.** A `data class` with `var` properties used as a key is lost when mutated.
- **Unkeyed hashing.** On the JVM, `String` and integer hashes are fixed, so chosen keys collide; `HashMap` tree bins help only `Comparable` keys (OpenJDK: O(log n) per bucket), not data-class keys or the Native and JS implementations. Worst case O(n) per lookup.
- **Sorts** (`sort`, `sortBy`, `sortedWith`, `Array<T>.sortWith`) are stable on every target. `sortedBy { }.reversed()` reverses equal elements; `sortedByDescending { }` keeps them. `binarySearch` may return any equal index. `maxBy`, `maxWith`, `minBy` return the first extreme; `sortedBy { }.last()` the last.
- **Sequences are lazy:** lambdas interleave element by element and run only at a terminal operation.
- **Strings are UTF-16:** `length` counts code units; `reversed()` splits surrogate pairs. Kotlin's `split(",")` is literal and keeps trailing empty strings; Java's `String.split` takes a regex and drops them.
- **Silent `Int` overflow,** including `sum()` on `List<Int>`; use `Long`, `sumOf { it.toLong() }`, or `Math.multiplyExact`.
- **Read-only is not immutable:** an internal `MutableList` returned as `List` can be mutated by Java callers.
- **`by lazy` is synchronized by default;** `LazyThreadSafetyMode.NONE` or `PUBLICATION` removes that guarantee.

## Testing, profiling, and benchmarking

- **Tests:** JUnit, `kotlin.test`, Kotest. Gradle scripts, `buildSrc`, convention plugins, and compiler plugins run code during the build; `gradlew` downloads the distribution its properties file names.
- **Property-based testing, if already present:** Kotest property testing, whose `Exhaustive` generators enumerate small domains (level 3); jqwik.
- **Profiling:** async-profiler or Java Flight Recorder on the JVM; `perf` or Instruments for Kotlin/Native.
- **Benchmarks:** kotlinx-benchmark or JMH if present (`-prof gc` for allocation); otherwise `System.nanoTime()` with warmup and medians.
- **Verification beyond tests** ("Verification levels" in `DIFFERENTIAL-TESTING.md`): Lincheck for linearizability of concurrent structures, with a model-checking mode; on the JVM, jcstress and JBMC from `JAVA.md`.
- **Constant-time comparison:** on the JVM, `MessageDigest.isEqual`, whose time depends only on its first argument's length, so pass the expected value first; not `contentEquals` or `==`.

## References

Sources: `references/languages/KOTLIN.md`.
