# References for `languages/SWIFT.md`

Sources for the claims in `languages/SWIFT.md`. Read only to verify a claim, on the page for the project's language and library version.

- Swift standard library: developer.apple.com/documentation/swift; sort stability: stdlib/public/core/Sort.swift in github.com/swiftlang/swift; geometric growth: "Preserving an Array's Geometric Growth Strategy" under `Array.reserveCapacity(_:)`
- Swift Collections package: github.com/apple/swift-collections; Swift Evolution SE-0453 (`InlineArray`), SE-0447 (`Span`), SE-0390 (noncopyable types)
- Sort closure calls, stability, and Timsort: stdlib/public/core/Sort.swift in github.com/swiftlang/swift. `ArraySlice` as a view: stdlib/public/core/ArraySlice.swift. Synthesized `hash(into:)`: stdlib/public/core/Hashable.swift.
- No public binary search in stdlib/public/core/CollectionAlgorithms.swift, whose partitioning-index helper is internal; `partitioningIndex(where:)`: Guides/Partition.md in github.com/apple/swift-algorithms. `NSCache`: Sources/Foundation/NSCache.swift in github.com/swiftlang/swift-corelibs-foundation. `@testable`: "Access Levels for Unit Test Targets" in TSPL.docc/LanguageGuide/AccessControl.md in github.com/swiftlang/swift-book.
- Swift Algorithms package: README.md (source stability) and Guides/ (MinMax.md, Unique.md, Partition.md, Keyed.md, Reductions.md, FirstNonNil.md, Windows.md, AdjacentPairs.md, Chunked.md) in github.com/apple/swift-algorithms.
