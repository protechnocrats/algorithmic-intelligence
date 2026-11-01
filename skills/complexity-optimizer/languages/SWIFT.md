# Swift

Load this file for Swift projects (iOS, macOS, server-side Swift). Record the Swift version and deployment target; some APIs below need newer versions.

## Built-in structures

| Structure | Swift API | Key costs | Notes |
|---|---|---|---|
| Dynamic array | `Array` | subscript O(1), `append` amortized O(1), `insert(at: 0)` and `removeFirst()` O(n), `contains` O(n) | Value type with copy-on-write |
| Slice | `ArraySlice` | O(1) to create | Shares storage and keeps the whole base array alive |
| Hash set | `Set` | insert/contains/remove O(1) average | Unordered; iteration order varies per process |
| Hash map | `Dictionary` | O(1) average | Unordered; iteration order varies per process |
| Flag set | `OptionSet` | O(1) set operations on a raw integer | Idiomatic bitmask |
| String | `String` | **`count` is O(n)**; index offsetting is O(n) | Indexed by `Character` (grapheme cluster) |
| Contiguous storage | `ContiguousArray` | Like `Array`, without Objective-C bridging | Small win for class element types |
| Lazy pipeline | `.lazy` | Avoids intermediate arrays | Changes evaluation order (see traps) |

### Not in the standard library

**Deque, heap/priority queue, ordered set, ordered dictionary, and sorted collections are not in the standard library.** Apple's `swift-collections` package provides `Deque`, `Heap`, `OrderedSet`, `OrderedDictionary`, `BitSet`, and `BitArray`, but it is a dependency: ask before adding it (rule 7). Check the current release for sorted collections before proposing them. Without the dependency:

- **Queue:** an array plus a head index (amortized O(1) dequeue), compacting occasionally.
- **Heap:** a small in-project binary heap with tests.
- **Ordered set:** an `Array` for order plus a `Set` for membership.

## Hidden costs

| Pattern | Cost | Fix |
|---|---|---|
| `array.removeFirst()` or `insert(_, at: 0)` in a loop (queue, BFS) | O(n) each, O(n²) total | Head index, reversed array with `popLast()`, or `Deque` (dependency) |
| `array.contains(x)` or `firstIndex(of:)` inside a loop | O(n·m) | `Set` or `Dictionary` built once |
| `s[s.index(s.startIndex, offsetBy: i)]` inside a loop | O(n) per access, O(n²) total | Iterate the string directly, or convert once with `Array(s)` or use `s.utf8`/`s.unicodeScalars` when the semantics allow |
| `string.count` in a loop condition | O(n) per evaluation | Compute once |
| Mutating an array that is also referenced elsewhere | Copy-on-write triggers a full O(n) copy | Ensure unique ownership; mutate in place with `inout`; avoid copying into a local `var` and mutating it |
| Arrays or large structs stored in a class property and mutated through a computed property or a getter that returns a copy | A copy on each mutation | Mutate the stored property directly |
| `reduce([]) { $0 + [$1] }` or `reduce("") { $0 + $1 }` | O(n²) | `reduce(into: [])`, `append`, `joined()` |
| `filter { }.count` or `filter { }.first` | Allocates an array | `first(where:)`, `contains(where:)`, `count(where:)` (Swift 6+) |
| `sorted()` inside a loop | O(n log n) per iteration | Sort once or maintain a heap |
| `NSRegularExpression` or `Regex` construction in a loop | Recompiles each time | Create once and reuse |
| `Array(dictionary.keys).sorted()` repeatedly | O(n log n) per call | Cache when the dictionary has not changed |
| `DateFormatter` / `NumberFormatter` creation in a loop or cell configuration | Expensive initialization | Reuse a shared formatter (they are thread-safe for formatting on modern OS versions) |

## iOS performance hot spots

- **Main thread.** Heavy work on the main actor causes dropped frames. Moving work off the main actor changes threading behavior, so ask first (rule 11).
- **SwiftUI.** `body` runs often; expensive computation there runs on every update. Move derived values into the model, cache them, or compute them when inputs change. Use stable `id`s in `ForEach` and `List`.
- **UIKit.** No heavy work in `cellForRowAt`, `layoutSubviews`, or `draw(_:)`. Use diffable data sources instead of `reloadData()` for small changes.
- **Core Data and SwiftData.** Fetches inside loops (N+1): fetch once with a predicate such as `IN`, use `relationshipKeyPathsForPrefetching`, and batch faults.

## Bit manipulation

| Operation | Swift |
|---|---|
| And, or, xor, not, shifts | `&`, `\|`, `^`, `~`, `<<`, `>>` |
| Popcount | `x.nonzeroBitCount` |
| Trailing / leading zeros | `x.trailingZeroBitCount`, `x.leadingZeroBitCount` |
| Wrapping arithmetic | `&+`, `&-`, `&*`, `&<<` |
| Flags | `struct Flags: OptionSet { let rawValue: UInt64 }` |

Swift's `<<` and `>>` are "smart shifts": overshifting gives 0 (or -1 for negative signed values with `>>`) rather than wrapping. `&<<` and `&>>` mask the shift count.

## Swift-specific traps

- **Hash iteration order changes per process.** `Set` and `Dictionary` use per-process random hash seeds, so iteration order can differ between runs. A rewrite that iterates a set where the original iterated an array may pass tests once and fail later. Never return or iterate a `Set`/`Dictionary` where order is observable.
- **Arithmetic overflow traps.** `+`, `-`, and `*` crash on overflow. A closed-form formula or different summation order can crash where the original did not.
- **Sort stability is not guaranteed by the documentation.** `sort()` and `sorted()` are stable in the current implementation, but the documentation does not promise it. If the original relied on stable ordering of equal elements, make the comparison total (add a tiebreaker) and test it.
- **Value versus reference semantics.** Arrays, dictionaries, sets, and strings are values. Replacing them with a class-based structure introduces shared mutation.
- **String length units.** `count` counts grapheme clusters; `utf8.count`, `utf16.count`, and `unicodeScalars.count` differ. Switching views to gain speed changes results for non-ASCII text.
- **Lazy sequences** run closures on demand and may run them more than once if iterated more than once.
- **`Equatable` versus `Hashable` consistency.** Custom types whose `==` and `hash(into:)` disagree break in sets and dictionaries.
- **Concurrency.** Moving to `async let` or task groups changes ordering and error behavior; actor isolation changes threading. Ask first.

## Testing and benchmarking

- **Tests:** XCTest and Swift Testing (`@Test`, `#expect`, Swift 6 / Xcode 16+).
- **Property-based testing, if already present:** SwiftCheck. Otherwise use a seeded generator (for example, a small linear-congruential or SplitMix generator conforming to `RandomNumberGenerator`) so cases reproduce.
- **Profiling:** Instruments (Time Profiler for CPU, Allocations and Leaks for memory, SwiftUI instrument for view-body updates) on a release build and a real device; `perf` or Valgrind on Linux.
- **Benchmarks:** XCTest `measure { }` with release-mode builds, or the `package-benchmark` package if already present (a dependency otherwise). Debug builds are dramatically slower and misleading.
- **Verification beyond tests** (see "Verification levels" in `DIFFERENTIAL-TESTING.md`): Thread Sanitizer (`-sanitize=thread`) for data races; the Swift 6 language mode's complete concurrency checking, which rejects data races at compile time. No mainstream bounded model checker targets Swift: reach level 3 by enumerating small domains exhaustively in tests.
- **Constant-time comparison** (for secrets; see `techniques/hostile-inputs.md`): CryptoKit's message-authentication-code and digest types compare in constant time with `==`; raw byte arrays do not, so compare those with a loop that combines every byte difference without exiting early, and verify it.

## References (for verifying claims; not required reading)

- Swift standard library: developer.apple.com/documentation/swift; Swift Collections package: github.com/apple/swift-collections
