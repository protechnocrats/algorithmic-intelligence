# Sources for `skills/languages/JAVA.md`

Where each claim in that file comes from, for maintainers and reviewers. Not part of the installed skill. Javadoc pages are under docs.oracle.com/en/java/javase/21/docs/api/java.base/ followed by the class path (for example `java/util/PriorityQueue.html`); replace `21` with the project's version. Source paths are under src/java.base/share/classes/ in github.com/openjdk/jdk.

## Built-in structures

- `ArrayList`, `LinkedList` (indexed access traverses), `ArrayDeque` (rejects `null`, faster than `Stack` and `LinkedList`): the class descriptions in `java/util/ArrayList.html`, `java/util/LinkedList.html`, `java/util/ArrayDeque.html`.
- `HashMap` tree bins and the role of `Comparable` keys: the "Implementation notes" comment in `java/util/HashMap.java` (implementation behavior, not specified by the Javadoc).
- Bounded LRU with access order and `removeEldestEntry`: `java/util/LinkedHashMap.html` (constructor with `accessOrder`, and `removeEldestEntry`).
- `TreeMap` as a red-black tree with O(log n) operations: `java/util/TreeMap.html`.
- `PriorityQueue` costs (O(log n) offer and poll, linear `remove(Object)` and `contains`, unordered iterator): "Implementation note" in `java/util/PriorityQueue.html`.
- `BitSet`, `EnumSet` (bit vector), `EnumMap` (array): `java/util/BitSet.html`, `java/util/EnumSet.html`, `java/util/EnumMap.html`. `CopyOnWriteArrayList` copying on write: `java/util/concurrent/CopyOnWriteArrayList.html`.
- `Collections.binarySearch` on a non-`RandomAccess` list doing O(n) link traversals: `java/util/Collections.html#binarySearch`.

## Packages

- Guava `MinMaxPriorityQueue` (costs, `null` rejection, eviction with a maximum size, the note on one-ended use) and `Comparators.least`/`greatest` (ties broken arbitrarily), `TreeMultiset`, `Multimap`: the class pages at guava.dev/releases/snapshot-jre/api/docs/.
- fastutil type-specific collections: fastutil.di.unimi.it and github.com/vigna/fastutil.
- Eclipse Collections and its Java 17 requirement for version 13: the release notes at github.com/eclipse-collections/eclipse-collections/releases.

## Hidden costs

- `Comparator.comparing` calling the extractor on both arguments: `java/util/Comparator.java`. Object sorts stable (TimSort): `java/util/Arrays.html#sort(java.lang.Object[])` and `java/util/List.html#sort`.
- `removeAll`/`retainAll` calling `contains` on the argument: `java/util/ArrayList.java` (`batchRemove`). `AbstractSet.removeAll` choosing a side by size: `java/util/AbstractSet.html#removeAll`.
- String concatenation in a loop: JLS 15.18.1 and JEP 280 (indified concatenation optimizes a single expression only).
- `String.split` fast path for one literal or escaped character: `java/lang/String.java` (`split`). `String.matches`, `replaceAll` compiling a `Pattern` each call: `java/lang/String.html#matches` and `#replaceAll` ("An invocation of this method … yields exactly the same result as `Pattern.matches`").
- `List.hashCode` over every element: `java/util/List.html#hashCode`. `String` caching its hash: `java/lang/String.java` (`hash` field). `Throwable` filling in its stack trace: `java/lang/Throwable.html#fillInStackTrace`. `subList` as a view: `java/util/List.html#subList`.
- `HashMap.computeIfAbsent` throwing `ConcurrentModificationException` when the function modifies the map (Java 9 and later): `java/util/HashMap.html#computeIfAbsent`. `ConcurrentHashMap.computeIfAbsent` ("must not attempt to update any other mappings of this map"): `java/util/concurrent/ConcurrentHashMap.html#computeIfAbsent`; the `IllegalStateException("Recursive update")`: `java/util/concurrent/ConcurrentHashMap.java`.

## Input handling and security

- `Integer.parseInt` (non-ASCII digits through `Character.digit`, leading `+`): `java/lang/Integer.html#parseInt(java.lang.String)`. `Integer.decode` (`0x`, `#`, leading-zero octal): `java/lang/Integer.html#decode`. `Double.parseDouble` grammar (whitespace trimmed, `NaN`, `Infinity`, hex, `d`/`f` suffix): `java/lang/Double.html#valueOf(java.lang.String)`.
- `Pattern.quote` and `Matcher.quoteReplacement`: `java/util/regex/Pattern.html#quote` and `java/util/regex/Matcher.html#quoteReplacement`.
- Locale-sensitive case mapping (Turkish `i`/`İ` and `I`/`ı`): `java/lang/String.html#toUpperCase()` and `#toLowerCase()`. Default charset UTF-8 from Java 18: JEP 400 (openjdk.org/jeps/400).
- `ObjectInputStream` and untrusted data: Secure Coding Guidelines for Java SE, section 8 "Serialization and Deserialization" (www.oracle.com/java/technologies/javase/seccodeguide.html), and JEP 290 (serialization filtering).

## Bit manipulation and traps

- Shift-count masking: JLS 15.19. Silent integer overflow: JLS 15.17 and 15.18.2; `Math.addExact`, `multiplyExact`: `java/lang/Math.html`.
- `Integer` cache of -128 to 127: JLS 5.1.7 and `java/lang/Integer.html#valueOf(int)`.
- `Map.of`, `Set.of` iteration order unspecified and randomized per run: "Unmodifiable Maps" in `java/util/Map.html` ("The iteration order of mappings is unspecified and is subject to change") and the `SALT` field in `java/util/ImmutableCollections.java`.
- `Arrays.asList` fixed-size: `java/util/Arrays.html#asList`. `List.of`, `Stream.toList()` (Java 16) unmodifiable: `java/util/List.html` and `java/util/stream/Stream.html#toList()`. `Collectors.toList()` guaranteeing nothing about mutability: `java/util/stream/Collectors.html#toList()`.
- Parallel streams, `forEach` versus `forEachOrdered`, `findAny`: `java/util/stream/package-summary.html` ("Ordering", "Parallelism"). Stream reuse throwing `IllegalStateException`: `java/util/stream/Stream.html` (class description) and `java/util/stream/AbstractPipeline.java`.
- `String.split` dropping trailing empty strings: `java/lang/String.html#split(java.lang.String)`.

## Testing and benchmarking

- JMH and `-prof gc`: github.com/openjdk/jmh (samples and profilers). async-profiler: github.com/async-profiler/async-profiler.
- JBMC: www.cprover.org/jbmc/. jcstress: github.com/openjdk/jcstress. Java PathFinder: github.com/javapathfinder/jpf-core. OpenJML: www.openjml.org.
- `MessageDigest.isEqual` timing and its early return for a `null` or empty second argument: the `@implNote` in `java/security/MessageDigest.html#isEqual` and bugs.openjdk.org/browse/JDK-8295919.
