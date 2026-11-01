# Java

Load this file for Java projects. Kotlin projects consult it only for JVM structures Kotlin does not provide (rule 14 and `KOTLIN.md`). Check the Java language level: some APIs below need newer versions.

## Built-in structures

| Structure | Java API | Key costs | Notes |
|---|---|---|---|
| Dynamic array | `ArrayList` | get/set O(1), add amortized O(1), add/remove at index 0 O(n), `contains` O(n) | |
| Linked list | `LinkedList` | add/remove at ends O(1), **`get(i)` O(n)** | Rarely the right choice; prefer `ArrayDeque` or `ArrayList` |
| Double-ended queue | `ArrayDeque` | push/pop/offer/poll at both ends O(1) amortized | Rejects `null`; faster than `Stack` and `LinkedList` |
| Hash map / set | `HashMap`, `HashSet` | O(1) average; for `Comparable` keys, colliding entries may be ordered by comparison (OpenJDK: O(log n) per crowded bucket); otherwise O(n) worst case | No order guarantee |
| Insertion-ordered | `LinkedHashMap`, `LinkedHashSet` | O(1) average | Preserves insertion order |
| Access-ordered bounded cache | `LinkedHashMap(cap, 0.75f, true)` + override `removeEldestEntry` | O(1) get/put | A built-in bounded LRU cache (rule 1) |
| Sorted map / set | `TreeMap`, `TreeSet` | O(log n); `floorKey`, `ceilingKey`, `headMap`, `subMap` | Red-black tree |
| Priority queue | `PriorityQueue` | offer/poll O(log n), peek O(1), **`remove(Object)` and `contains` O(n)** | Binary min-heap; iteration order is not sorted |
| Bitset | `BitSet` | O(1) per bit; `and`, `or`, `cardinality`, `nextSetBit` | Grows automatically |
| Enum set / map | `EnumSet`, `EnumMap` | O(1), bit-vector backed | Ideal for flag sets |
| Concurrent | `ConcurrentHashMap`, `ConcurrentLinkedDeque`, `CopyOnWriteArrayList` | `CopyOnWriteArrayList` writes are O(n) | Keep thread-safety when replacing |
| Search / sort helpers | `Arrays.sort`, `Collections.sort`, `Arrays.binarySearch`, `Collections.binarySearch` | O(n log n), O(log n) | `Collections.binarySearch` on a `LinkedList` is O(n) |
| String building | `StringBuilder`, `String.join`, `Collectors.joining` | append amortized O(1) | |

Not in the standard library: multisets, bidirectional maps, primitive-specialized collections, interval trees, tries. Primitive collections (fastutil, Eclipse Collections) and Guava are dependencies; ask first (rule 7).

## Hidden costs

| Pattern | Cost | Fix |
|---|---|---|
| `LinkedList.get(i)` in an indexed loop | O(n²) | Iterate with an iterator or switch to `ArrayList` |
| `list.remove(0)` on `ArrayList` as a queue | O(n) per removal | `ArrayDeque` |
| `list.contains(x)` inside a loop | O(n·m) | `HashSet` built once |
| `a.removeAll(b)` / `retainAll(b)` where `b` is a `List` | O(n·m) | Pass a `HashSet`. For `AbstractSet.removeAll`, cost depends on which collection is larger |
| `String s += x` in a loop | O(n²) copying (the compiler only optimizes single expressions) | `StringBuilder` |
| `Pattern.compile` or `String.matches`/`replaceAll`/`split` with a regex in a hot loop | Recompiles each call | Precompiled `static final Pattern` |
| `String.format` in hot paths | Parses the format each call | `StringBuilder` |
| `Map<Integer, Integer>`, `List<Long>` in hot numeric code | Boxing, GC pressure, cache misses | Primitive arrays or counting arrays |
| `stream()` pipelines in very hot tight loops | Allocation overhead | Plain loop, only if a benchmark shows it matters |
| `Vector`, `Hashtable`, `Stack`, `StringBuffer` | Synchronization on every call | Unsynchronized equivalents, only when not shared across threads |
| `priorityQueue.remove(obj)` to update a priority | O(n) | Lazy deletion (push new entry, skip stale ones on poll) or an indexed heap |
| `map.containsKey(k)` followed by `map.get(k)` | Two lookups | `get` with null check, `getOrDefault`, `computeIfAbsent`, `merge` (only when `null` values are not meaningful) |

## Bit manipulation

| Operation | Java |
|---|---|
| And, or, xor, not, shifts | `&`, `\|`, `^`, `~`, `<<`, `>>` (arithmetic), `>>>` (logical) |
| Popcount | `Integer.bitCount(x)`, `Long.bitCount(x)` |
| Trailing / leading zeros | `Integer.numberOfTrailingZeros`, `Integer.numberOfLeadingZeros` |
| Lowest / highest set bit | `Integer.lowestOneBit`, `Integer.highestOneBit` |
| 64 flags | `long` with `1L << i` (`1 << i` is an `int` and wraps at 32) |

Shift counts are masked (`1 << 32 == 1` for `int`).

## Java-specific traps

- **`HashMap`/`HashSet` order** is unspecified and changes with capacity and Java version. `LinkedHashMap` keeps insertion order.
- **Sort stability:** `Arrays.sort(Object[])`, `Collections.sort`, and `List.sort` are stable (TimSort). `Arrays.sort` on primitives is not stable, but stability is not observable for primitives.
- **`Integer` caching:** `==` on boxed `Integer` compares references and works only for values -128 to 127 by default. A rewrite that changes boxing can change `==` results.
- **`equals` without `hashCode`** works in lists but fails in hash structures.
- **`Arrays.asList`** is fixed-size; `List.of` and `Stream.toList()` (Java 16+) are unmodifiable; `Collectors.toList()` makes no guarantee about mutability but returns an `ArrayList` in practice. Changing which one is returned changes what callers can do.
- **`ConcurrentModificationException`** when modifying a collection while iterating it with for-each; use `removeIf` or an explicit iterator.
- **Nulls:** `ArrayDeque`, `TreeMap` (natural ordering), `ConcurrentHashMap`, `List.of`, and `Map.of` reject `null`; `ArrayList` and `HashMap` accept it.
- **`Map.of` and `Set.of` iteration order is randomized** per JVM run.
- **Silent overflow** in `int` and `long` arithmetic; `Math.addExact` and `Math.multiplyExact` throw instead.

## Testing and benchmarking

- **Tests:** JUnit 5 (or 4), AssertJ, Mockito.
- **Property-based testing, if already present:** jqwik, junit-quickcheck.
- **Profiling:** async-profiler (CPU, allocation, and lock flame graphs) or Java Flight Recorder (`-XX:StartFlightRecording`, viewed in JDK Mission Control); VisualVM if nothing else is available.
- **Benchmarks, if already present:** JMH (`-prof gc` reports allocation per operation). Otherwise use a timing harness with warmup in test code; note that JIT warmup, dead-code elimination, and GC make naive timings unreliable.
- **Verification beyond tests** (see "Verification levels" in `DIFFERENTIAL-TESTING.md`; ask unless present): JBMC for bounded model checking of bytecode, including equivalence harnesses; jcstress for concurrency outcomes under the Java memory model; Java PathFinder for model checking thread interleavings; OpenJML for checking JML contracts.
- **Constant-time comparison** (for secrets; see `techniques/hostile-inputs.md`): `MessageDigest.isEqual` (time depends only on the first argument's length), never `Arrays.equals` or `String.equals` on secrets.

## References (for verifying claims; not required reading)

- Java collections API: docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/package-summary.html
