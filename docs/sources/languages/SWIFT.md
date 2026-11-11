# Sources for `skills/algorithmic-intelligence/references/languages/SWIFT.md`

Where each claim in that file comes from, for maintainers and reviewers. Not part of the installed skill. Apple documentation pages are under developer.apple.com/documentation/ followed by the path given. Source paths are in github.com/swiftlang/swift unless another repository is named. "TSPL" is *The Swift Programming Language* (docs.swift.org/swift-book/).

## Built-in structures

- `Array` costs, copy-on-write, and `reserveCapacity`'s growth warning: `swift/array` and "Preserving an Array's Geometric Growth Strategy" under `swift/array/reservecapacity(_:)`.
- `ArraySlice` sharing storage and keeping its base's indices: `swift/arrayslice` and stdlib/public/core/ArraySlice.swift. `Substring`: `swift/substring`.
- `Set` and `Dictionary` seeded hashing: `swift/hasher` ("random seed"). `OptionSet`: `swift/optionset`.
- `String.count` and index offsetting as O(n), grapheme clusters: `swift/string` and TSPL, "Strings and Characters".
- `ContiguousArray`: `swift/contiguousarray`.
- `InlineArray` (Swift 6.2) and its availability: SE-0453 (in github.com/swiftlang/swift-evolution) and `swift/inlinearray`. `Span`, `MutableSpan`: SE-0447 and SE-0467. Noncopyable types, `borrowing`/`consuming` (5.9): SE-0390 and SE-0377.

## Not in the standard library and packages

- swift-collections (`Deque`, `Heap`, `OrderedSet`, `OrderedDictionary`, `BitSet`, `BitArray`, `TreeSet`, `TreeDictionary`, `RigidArray`; sorted collections unreleased): README and release notes at github.com/apple/swift-collections.
- No public binary search: stdlib/public/core/CollectionAlgorithms.swift, whose partitioning-index helper is internal.
- `NSCache` in swift-corelibs-foundation (eviction by cost, reads not reordering): Sources/Foundation/NSCache.swift in github.com/swiftlang/swift-corelibs-foundation; Apple's `foundation/nscache` documents no eviction order.
- swift-algorithms (source stability, and each API's cost and behavior): README.md and Guides/ (Partition.md, MinMax.md, Unique.md, Keyed.md, Reductions.md, FirstNonNil.md, Windows.md, AdjacentPairs.md, Chunked.md) in github.com/apple/swift-algorithms.

## Hidden costs

- `dict[k, default:]` mutating in place: `swift/dictionary/subscript(_:default:)`.
- `count(where:)` (Swift 6.0): SE-0220.
- Sort closure calls and stability: stdlib/public/core/Sort.swift; stability documented in `swift/mutablecollection/sort(by:)` ("The sorting algorithm is guaranteed to be stable").
- Synthesized `hash(into:)` over every stored property: TSPL, "Protocols" ("Adopting a Protocol Using a Synthesized Implementation") and stdlib/public/core/Hashable.swift.
- Existentials, generic specialization, and `some`: TSPL, "Opaque and Boxed Protocol Types". Cross-module optimization and `@inlinable` under library evolution: docs/CrossModuleOptimization.md and docs/LibraryEvolution.rst.
- Global and `static let` initialized lazily and thread-safely: TSPL, "Properties" ("Type Properties").

## Input handling and security

- `Int(_:)` from a string: the `LosslessStringConvertible` initializer on the `swift/int` page. `Double(_:)` accepting `nan`, `inf`, and hex: `swift/double/init(_:)` (the `StringProtocol` initializer).
- `Decimal(string:)` without a locale differing by platform: bugs.swift.org SR-10525 and the Swift Forums thread "Why unable to debug Step Into Decimal(string:locale:)?" (forums.swift.org/t/53938); prefix parsing: `foundation/nsdecimalnumber/init(string:)`.
- `Character.isNumber`: `swift/character/isnumber`.
- `NSRegularExpression.escapedPattern(for:)`: `foundation/nsregularexpression/escapedpattern(for:)`.
- Fixed-format dates with `en_US_POSIX`: Technical Q&A QA1480 (developer.apple.com/library/archive/qa/qa1480/).
- `NSKeyedUnarchiver` and secure coding: `foundation/nskeyedunarchiver` and `foundation/nssecurecoding`.

## Bit manipulation and traps

- `nonzeroBitCount`, `trailingZeroBitCount`, `leadingZeroBitCount`: `swift/binaryinteger`. Overflow operators and overflow trapping: TSPL, "Advanced Operators". Smart shifts and masking shifts: SE-0104.
- `SWIFT_DETERMINISTIC_HASHING`: stdlib/public/core/Hashing.swift and the `swift/hasher` documentation.
- `Dictionary(uniqueKeysWithValues:)` trapping on duplicates: `swift/dictionary/init(uniquekeyswithvalues:)`.
- `Int` width by platform (32 bits on arm64_32): TSPL, "The Basics" ("Integers").
- `-Ounchecked`: docs/OptimizationTips.rst.
- String canonical equivalence: TSPL, "Strings and Characters" ("String and Character Equality").
- Exclusivity: TSPL, "Memory Safety". Actor reentrancy: TSPL, "Concurrency" ("Actors") and SE-0306.
- Embedded Swift restrictions: docs/EmbeddedSwift/ (the user manual and status pages).

## Testing and benchmarking

- Swift Testing (`@Test(arguments:)`): developer.apple.com/documentation/testing. `@testable import`: TSPL, "Access Control" ("Access Levels for Unit Test Targets").
- SwiftPM plugins and macros running during the build: github.com/swiftlang/swift-package-manager, Documentation/Plugins.md.
- package-benchmark: github.com/ordo-one/package-benchmark.
- Complete concurrency checking in Swift 6 mode: "Migrating to Swift 6" (swift.org/migration/documentation/migrationguide/).
- CryptoKit constant-time comparison of MACs and digests: `cryptokit/hashedauthenticationcode` and the `Digest` protocol pages.
