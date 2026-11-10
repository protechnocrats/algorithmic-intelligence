# Sources for `skills/languages/KOTLIN.md`

Where each claim in that file comes from, for maintainers and reviewers. Not part of the installed skill. API pages are under kotlinlang.org/api/core/kotlin-stdlib/ followed by the package and the function name in lowercase with hyphens (for example `kotlin.collections/get-or-put.html`). Source paths are in github.com/JetBrains/kotlin. Claims marked *(measured)* in the skill file have no published source; they were measured on Kotlin 2.4.

## Targets

- Kotlin/JS representation of `Long`: "Kotlin types in JavaScript" in kotlinlang.org/docs/js-to-kotlin-interop.html, and the "What's new" pages for Kotlin 2.2 and later (kotlinlang.org/docs/whatsnew2220.html and its successors) for the experimental `BigInt` mode; its exact conditions were not confirmed when this entry was written.
- Kotlin collections passed to Swift and Objective-C: the mapped-types table in kotlinlang.org/docs/native-objc-interop.html.
- Multiplatform `expect`/`actual`: kotlinlang.org/docs/multiplatform-expect-actual.html.

## Kotlin first and built-in structures

- `ArrayList`, `HashMap`, `HashSet`, `LinkedHashMap`, `LinkedHashSet`, `StringBuilder` as Kotlin types (type aliases on the JVM): the class pages `kotlin.collections/-array-list/`, `kotlin.collections/-hash-map/`, `kotlin.text/-string-builder/`, each listing its platforms.
- `sortedMapOf` returning `SortedMap` and `sortedSetOf` returning `java.util.TreeSet`: `kotlin.collections/sorted-map-of.html` and `kotlin.collections/sorted-set-of.html`.
- `ArrayDeque` (both ends, indexed access): `kotlin.collections/-array-deque/`.
- Insertion order of `setOf`, `mapOf`, `mutableMapOf`, `toSet`, `groupBy`, `associate*`: each function's API page ("preserves the … iteration order"); kotlinlang.org/docs/collections-overview.html.
- `listOf` read-only, not immutable: kotlinlang.org/docs/collections-overview.html ("Collection types").
- Sequences and evaluation order: kotlinlang.org/docs/sequences.html.
- kotlinx.collections.immutable (experimental API; `persistentSetOf` and `persistentMapOf` ordered, `persistentHash*` not): README and proposal at github.com/Kotlin/kotlinx.collections.immutable.
- androidx.collection (`LruCache`, `ScatterMap`, `MutableIntList`, `LongSparseArray`, `SieveCache`) and its platforms: developer.android.com/reference/kotlin/androidx/collection/package-summary and the module metadata on Google Maven (maven.google.com, group `androidx.collection`).

## Hidden costs

- `minus`, `removeAll`, `retainAll` with a `List` argument, the change in Kotlin 1.6, and the `kotlin.collections.convert_arg_to_set_in_removeAll` property: the `minus` page (`kotlin.collections/minus.html`) and the `removeAll` page (`kotlin.collections/remove-all.html`); implementation in libraries/stdlib/common/src/generated/_Collections.kt and libraries/stdlib/src/kotlin/collections/MutableCollections.kt.
- `sortedBy` and `compareBy` calling the selector on both elements each comparison: libraries/stdlib/src/kotlin/comparisons/Comparisons.kt (`compareValuesBy`). Sort stability: `kotlin.collections/sort-with.html` and `kotlin.collections/sorted-by.html` ("The sort is stable").
- `drop` building a new list: libraries/stdlib/common/src/generated/_Collections.kt. `subList` as a view: `kotlin.collections/-list/sub-list.html`.
- `groupingBy` and `eachCount`: kotlinlang.org/docs/collection-grouping.html.
- `toIntOrNull`: `kotlin.text/to-int-or-null.html`.
- Data class `equals` and `hashCode` over every primary-constructor property: kotlinlang.org/docs/data-classes.html.
- Boxing of `value class` in generic and nullable positions: kotlinlang.org/docs/inline-classes.html ("Representation").
- Spread operator copying the array: kotlinlang.org/docs/functions.html ("Variable number of arguments"); the copy itself is *(measured)*.

## Input handling and security

- `toInt` on the JVM delegating to `Integer.parseInt`: libraries/stdlib/jvm/src/kotlin/text/StringNumberConversionsJVM.kt; see `docs/sources/languages/JAVA.md` for what that accepts.
- `Regex.escape` and `Regex.escapeReplacement`: `kotlin.text/-regex/-companion/escape.html` and `escape-replacement.html`.
- `uppercase()` and `lowercase()` using the invariant locale: `kotlin.text/uppercase.html`. `String.format` using the default locale: `kotlin.text/format.html`.
- `DeepRecursiveFunction`: `kotlin/-deep-recursive-function/`.

## Bit manipulation

- `countOneBits`, `countTrailingZeroBits`, `countLeadingZeroBits`, `takeLowestOneBit`, `takeHighestOneBit`: the pages under `kotlin/` (for example `kotlin/count-one-bits.html`).
- `shl` and `ushr` masking the shift count, `%` versus `mod`: kotlinlang.org/docs/numbers.html ("Bitwise operations") and `kotlin/mod.html`.

## Kotlin-specific traps

- `associateBy` and `toMap` keeping the last value: `kotlin.collections/associate-by.html` and `kotlin.collections/to-map.html`.
- `getOrPut` treating `null` as missing: `kotlin.collections/get-or-put.html`. `getOrPutIfMissing` and `getOrPutIfNull` (Kotlin 2.4): `kotlin.collections/get-or-put-if-missing.html` and `get-or-put-if-null.html`. `getOrPut` on a `ConcurrentMap`: `kotlin.collections/java.util.concurrent.-concurrent-map/get-or-put.html`.
- Floating-point equality by static type: kotlinlang.org/docs/numbers.html#floating-point-numbers-comparison. `maxOrNull` returning `NaN`: `kotlin.collections/max-or-null.html`. The data-class case is *(measured)*.
- Arrays compared by reference and `contentEquals`: kotlinlang.org/docs/arrays.html ("Compare arrays").
- `maxBy` returning the first extreme: `kotlin.collections/max-by.html`. `binarySearch` returning any equal index: `kotlin.collections/binary-search.html`.
- `reversed()` keeping surrogate pairs: `kotlin.text/-string-builder/reverse.html` (which `CharSequence.reversed()` uses).
- Kotlin's `split` versus Java's: `kotlin.text/split.html`.
- `by lazy` synchronization modes: kotlinlang.org/docs/delegated-properties.html ("Lazy properties") and `kotlin/-lazy-thread-safety-mode/`.

## Testing and benchmarking

- `internal` visible to the test source set: kotlinlang.org/docs/visibility-modifiers.html ("Modules"). `internal` from Java and member name mangling: kotlinlang.org/docs/java-to-kotlin-interop.html ("Visibility").
- Kotest property testing and `Exhaustive` generators: kotest.io, "Property-based testing" documentation.
- kotlinx-benchmark: github.com/Kotlin/kotlinx-benchmark. Lincheck and its model-checking mode: github.com/JetBrains/lincheck.
- `MessageDigest.isEqual`: see `docs/sources/languages/JAVA.md`.
