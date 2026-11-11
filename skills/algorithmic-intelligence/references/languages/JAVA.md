# Java

Record the Java language level; some APIs below need newer versions. Kotlin projects use this file only for JVM structures Kotlin lacks (rule 14, `KOTLIN.md`).

**Contents:** Built-in structures · Hidden costs · Bit manipulation · Java-specific traps · Testing and benchmarking

## Built-in structures

| Structure | Java API | Key costs | Notes |
|---|---|---|---|
| Dynamic array | `ArrayList` | get/set O(1), add amortized O(1), add/remove at 0 O(n), `contains` O(n) | |
| Linked list | `LinkedList` | ends O(1), `get(i)` O(n) | Rarely right; prefer `ArrayDeque` or `ArrayList`. No node handles, so a middle insert needs a live `ListIterator` |
| Double-ended queue | `ArrayDeque` | both ends O(1) amortized | Rejects `null`; faster than `Stack` and `LinkedList` |
| Hash map / set | `HashMap`, `HashSet` | O(1) average; colliding `Comparable` keys may be tree-binned (OpenJDK: O(log n) per crowded bucket), otherwise O(n) worst case | No order guarantee |
| Insertion-ordered | `LinkedHashMap`, `LinkedHashSet` | O(1) average | |
| Bounded LRU cache | `LinkedHashMap(cap, 0.75f, true)` overriding `removeEldestEntry` | O(1) | Built in |
| Sorted map / set | `TreeMap`, `TreeSet` | O(log n); `floorKey`, `ceilingKey`, `headMap`, `subMap` | Red-black tree |
| Priority queue | `PriorityQueue` | offer/poll O(log n), peek O(1), `remove(Object)` and `contains` O(n) | Min-heap; iteration order not sorted |
| Bitset | `BitSet` | O(1) per bit; `and`, `or`, `cardinality`, `nextSetBit` | Grows automatically |
| Enum set / map | `EnumSet`, `EnumMap` | O(1); a bit vector and an ordinal-indexed array | Flag sets |
| Concurrent | `ConcurrentHashMap`, `ConcurrentLinkedDeque`, `CopyOnWriteArrayList` | `CopyOnWriteArrayList` writes O(n) | Keep thread-safety when replacing |
| Search / sort | `Arrays.sort`, `Collections.sort`, `binarySearch` | O(n log n), O(log n) | `Collections.binarySearch` on a `LinkedList` is O(n) |

Not in the standard library: multisets, bidirectional maps, primitive collections, interval trees, tries (fastutil, Eclipse Collections, Guava are dependencies).

### Packages

These are dependencies (rule 7). Besides what the project declares and what the developer names, they are the only packages to consider, whether or not the module's manifest declares them: use a declared one like the standard library, and propose an undeclared one when it beats what the standard library offers ("When the best technique is not available" in `ALGORITHM-ARSENAL.md`).

| Package | Provides | Watch for |
|---|---|---|
| `com.google.guava:guava` | `MinMaxPriorityQueue` (add and poll O(log n)), `TreeMultiset`, `Multimap`, and `Comparators.least`/`greatest` collectors for top-k | Top-k collectors break ties arbitrarily. `MinMaxPriorityQueue` is not thread-safe and rejects `null`; with a maximum size it evicts the greatest element, possibly the one just added, and its docs call one-ended use significantly worse than `PriorityQueue` with manual eviction. A `TreeMultiset` comparator must be consistent with `equals` |
| `it.unimi.dsi:fastutil` | Type-specific maps, sets, lists, and queues, with no boxing | Check its docs for the class names per type |
| `org.eclipse.collections:eclipse-collections` | Primitive lists, sets, bags, stacks, and maps; `Bag`, `Multimap`, `BiMap` | Version 13 needs Java 17 or later |

## Hidden costs

| Pattern | Cost | Fix |
|---|---|---|
| `LinkedList.get(i)` in an indexed loop | O(n²) | Iterator, or `ArrayList` |
| `ArrayList.remove(0)` as a queue | O(n) per removal | `ArrayDeque` |
| `list.contains(x)` in a loop | O(n·m) | `HashSet` built once |
| `removeAll(b)` / `retainAll(b)` with `b` a `List` | O(n·m) | Pass a `HashSet`; `AbstractSet.removeAll` cost depends on which side is larger |
| `s += x` in a loop | O(n²) (the compiler optimizes single expressions only) | `StringBuilder` |
| `Pattern.compile`, `String.matches`/`replaceAll`/`split` in a hot loop | Recompiles each call, except `split` on one literal or escaped character (a no-regex fast path) | `static final Pattern`; leave single-character `split` alone |
| `String.format` in hot paths | Parses the format each call | `StringBuilder` |
| `Comparator.comparing(x -> parse(x))` | The extractor runs for both elements on every comparison, with no caching | Compute keys first into a small record of key and element, sort, unwrap (object sorts are stable, so ties keep their order). Not needed for a field read |
| `new ArrayList<>(list.subList(1, n))` in recursion | Copies each call: O(n²) | Pass indices, or `subList` (a view) |
| A `List`, or a record holding one, as a `HashMap` key | `List.hashCode` walks every element on each call; only `String` caches its hash | A small ID or a `String` key built once |
| `Integer.parseInt` in `try`/`catch` in a hot loop | A `Throwable` fills in its stack trace per failed parse | A check first that accepts exactly the same strings (see "Number parsing") |
| `Map<Integer, Integer>`, `List<Long>` in hot numeric code | Boxing, GC, cache misses | Primitive or counting arrays |
| `Vector`, `Hashtable`, `Stack`, `StringBuffer` | Synchronization per call | Unsynchronized equivalents, only when not shared across threads |
| `priorityQueue.remove(obj)` to update a priority | O(n) | Lazy deletion or an indexed heap |
| `containsKey` then `get` | Two lookups | `getOrDefault`, `computeIfAbsent`, `merge` (only when `null` values mean nothing; the mapping function must not touch the map: recursive memoization through `computeIfAbsent` throws `ConcurrentModificationException` on `HashMap` and `IllegalStateException` or deadlocks on `ConcurrentHashMap`) |

### Input handling and security

- **Number parsing.** `Integer.parseInt`/`Long.parseLong` accept non-ASCII digits (`"٥"` is 5) and a leading `+`, but no whitespace or underscores; `Integer.decode` also accepts `0x` and leading-zero octal. `Double.parseDouble` trims whitespace and accepts `NaN`, `Infinity`, hex floats, and a trailing `d` or `f`. A fast parser has to match, including `NumberFormatException` on overflow.
- **`java.util.regex` backtracks.** Quote input in a pattern with `Pattern.quote`, and in a `replaceAll` replacement with `Matcher.quoteReplacement` (`$` and `\` are special).
- **Unkeyed hashing.** `String.hashCode` and boxed-integer hashes are fixed, so chosen keys collide; only `Comparable` keys get O(log n) lookups in a tree bin (non-`Comparable` keys with one hash are searched linearly). Worst case O(n) per lookup for untrusted non-`Comparable` keys.
- **Default locale, charset, and time zone are hidden inputs.** `toUpperCase()`/`toLowerCase()` without a `Locale` follow Turkish rules there (`"i".toUpperCase()` is dotted `İ`, `"I".toLowerCase()` is dotless `ı`); `String.format` uses the default locale's decimal separator; date formatting uses the default zone; the default charset is UTF-8 only from Java 18. New code passes `Locale.ROOT`, a charset, and a `ZoneId`.
- **Deserialization and recursion.** `ObjectInputStream.readObject` on untrusted data can run code. `StackOverflowError` depth depends on thread stack size and JIT state.

## Bit manipulation

| Operation | Java |
|---|---|
| And, or, xor, not, shifts | `&`, `\|`, `^`, `~`, `<<`, `>>` (arithmetic), `>>>` (logical) |
| Popcount | `Integer.bitCount`, `Long.bitCount` |
| Trailing / leading zeros | `Integer.numberOfTrailingZeros`, `numberOfLeadingZeros` |
| Lowest / highest set bit | `Integer.lowestOneBit`, `highestOneBit` |
| 64 flags | `long` with `1L << i` (`1 << i` is an `int`) |

Shift counts are masked (`1 << 32 == 1` for `int`).

## Java-specific traps

- **`HashMap`/`HashSet` order** changes with capacity and Java version; `Map.of` and `Set.of` order is randomized per JVM run.
- **Sort stability:** object sorts (`Arrays.sort(Object[])`, `Collections.sort`, `List.sort`) are stable TimSort; primitive sorts are not, which is unobservable.
- **`Integer` caching:** `==` on boxed values compares references and works only for -128 to 127 by default; changing boxing changes `==` results.
- **`remove` overloads:** on a `List<Integer>`, `remove(int)` removes by index and `remove(Integer)` by value.
- **`equals` without `hashCode`** works in lists, fails in hash structures.
- **Returned list mutability:** `Arrays.asList` is fixed-size; `List.of` and `Stream.toList()` (16+) are unmodifiable; `Collectors.toList()` guarantees nothing but returns an `ArrayList` in practice.
- **Nulls:** `ArrayDeque`, `TreeMap` (natural ordering), `ConcurrentHashMap`, `List.of`, `Map.of` reject `null`; `ArrayList` and `HashMap` accept it.
- **`ConcurrentModificationException`** when modifying during for-each; `removeIf` or an iterator instead.
- **Silent `int`/`long` overflow;** `Math.addExact` and `multiplyExact` throw instead.
- **Parallel streams:** `forEach` loses encounter order (`forEachOrdered` keeps it), `findAny` differs from `findFirst`, and work runs on the shared common pool.
- **`String.split` drops trailing empty strings** and takes a regex.
- **A `Stream` is single-use:** a second terminal operation throws `IllegalStateException`; a `Supplier<Stream>` runs the whole pipeline again.

## Testing and benchmarking

- **Tests:** JUnit 5 or 4, AssertJ, Mockito. Gradle scripts (`build.gradle(.kts)`, `settings.gradle`, `buildSrc`, plugins, init scripts) and Maven plugins bound to the test phase run code; `gradlew` downloads the distribution named in `gradle-wrapper.properties`.
- **Testing an extracted function:** package-private, with the test in the same package.
- **Property-based testing, if already present:** jqwik, junit-quickcheck.
- **Profiling:** async-profiler (CPU, allocation, lock flame graphs) or Java Flight Recorder; VisualVM otherwise.
- **Benchmarks:** JMH if already present (`-prof gc` for allocation). Otherwise a harness with warmup; JIT warmup, dead-code elimination, and GC make naive timings unreliable.
- **Verification beyond tests** ("Verification levels" in `DIFFERENTIAL-TESTING.md`): JBMC (bounded model checking of bytecode, including equivalence harnesses); jcstress (outcomes under the memory model); Java PathFinder (thread interleavings); OpenJML (JML contracts).
- **Constant-time comparison:** `MessageDigest.isEqual` (time depends only on the first argument's length, except that it returns at once when the second is `null` or empty). `Arrays.equals` and `String.equals` stop at the first difference.
