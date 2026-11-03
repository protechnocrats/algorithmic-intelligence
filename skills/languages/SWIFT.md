# Swift

Load this file for Swift projects on any target: Apple platforms, Linux and Windows, WebAssembly, and microcontrollers (Embedded Swift). Record the Swift version, the target, and the optimization mode: several APIs below need Swift 5.9 or 6.2, and `Int` is 32 bits on some targets (traps).

## Built-in structures

| Structure | Swift API | Key costs | Notes |
|---|---|---|---|
| Dynamic array | `Array` | subscript O(1), `append` amortized O(1), `insert(at: 0)` and `removeFirst()` O(n), `contains` O(n) | Value type with copy-on-write |
| Slice | `ArraySlice`, `Substring` | O(1) to create | Shares storage and keeps the whole base alive; **indices are not zero-based** (traps) |
| Hash set / map | `Set`, `Dictionary` | O(1) expected | Unordered; seeded per process (traps) |
| Flag set | `OptionSet` | O(1) set operations on a raw integer | Idiomatic bitmask |
| String | `String` | **`count` is O(n)**; index offsetting is O(n) | Indexed by `String.Index`, iterates `Character` (grapheme clusters) |
| Contiguous storage | `ContiguousArray` | Like `Array`, without Objective-C bridging | Matters only on Apple platforms with class elements |
| Fixed-size inline array | `InlineArray<N, T>` (Swift 6.2+; on Apple platforms also an OS 26 deployment target, since it is not back-deployed) | O(1), no heap allocation | Size fixed at compile time; for small buffers and embedded targets |
| Borrowed view | `Span`, `MutableSpan` (Swift 6.2+) | O(1) access, no copy, no reference counting | Safe replacement for `withUnsafeBufferPointer` in hot loops |
| Unique ownership | `~Copyable` types, `borrowing`/`consuming` parameters (Swift 5.9+) | No implicit copies or copy-on-write checks | Changes how callers can use the type: a public-contract change (rule 11) |
| Lazy pipeline | `.lazy` | Avoids intermediate arrays | Changes evaluation order (traps) |

### Not in the standard library

**Deque, heap, ordered set and dictionary, bitset, and sorted collections are not in the standard library.** Apple's `swift-collections` package provides `Deque`, `Heap`, `OrderedSet`, `OrderedDictionary`, `BitSet`, `BitArray`, `TreeSet` and `TreeDictionary` (persistent hash tries: cheap copies with structural sharing), and fixed-capacity `RigidArray`. Its `SortedSet` and `SortedDictionary` are an unstable preview, not a release. The package is a dependency: ask before adding it (rule 7). Without it:

- **Queue:** an array plus a head index (amortized O(1) dequeue), compacting occasionally.
- **Heap:** a small in-project binary heap with tests.
- **Ordered set:** an `Array` for order plus a `Set` for membership.

## Hidden costs

This table lists common traps, not every operation. Unlisted calls also count at their real cost ("Count every call at its real cost" under rule 6 in `SKILL.md`).

| Pattern | Cost | Fix |
|---|---|---|
| `array.removeFirst()` or `insert(_, at: 0)` in a loop (queue, BFS) | O(n) each, O(n²) total | Head index, reversed array with `popLast()`, or `Deque` (dependency) |
| `array.contains(x)` or `firstIndex(of:)` inside a loop | O(n·m) | `Set` or `Dictionary` built once (traps: duplicate keys, string equality) |
| `var a = dict[k] ?? []; a.append(x); dict[k] = a` | Copies the whole array each update: O(n²) | Mutate in place: `dict[k, default: []].append(x)` |
| `s[s.index(s.startIndex, offsetBy: i)]` inside a loop | O(n) per access, O(n²) total | Iterate the string directly, convert once with `Array(s)`, or use `s.utf8` when the semantics allow |
| `string.count` in a loop condition | O(n) per evaluation | Compute once |
| Mutating a value that is also referenced elsewhere | Copy-on-write makes a full O(n) copy | Ensure unique ownership; mutate in place with `inout`; do not copy into a local `var` to mutate it |
| Arrays or large structs mutated through a computed property or a getter that returns a copy | A copy on each mutation | Mutate the stored property directly |
| `reduce([]) { $0 + [$1] }` or `reduce("") { $0 + $1 }` | O(n²) | `reduce(into: [])`, `append`, `joined()` |
| `reserveCapacity(count + k)` on each call or batch | Allocates only what is asked, so growth turns linear: each call can cost O(n), O(n²) overall. On bridged storage it always copies | Remove the call and let `append` grow the array, reserve once with the final size, or compute a geometric size yourself |
| `filter { }.count` or `filter { }.first` | Allocates an array | `first(where:)`, `contains(where:)`, `count(where:)` (Swift 6+) |
| `sorted()` inside a loop | O(n log n) per iteration | Sort once or maintain a heap |
| `any Protocol` values or unspecialized generics in a hot loop | Dynamic dispatch, boxing, no inlining | Generics or `some Protocol`; across modules, specialization needs `@inlinable`, an ABI change: ask |
| Class instances in hot loops | Retain and release per access; copying a struct retains every class reference it holds | Structs, `final` or `private` classes (devirtualization), or fewer references per element |
| Regex, formatter, or `JSONDecoder` construction in a loop | Expensive initialization | Create once outside the loop. A global or `static let` is initialized lazily and thread-safely, but a shared formatter captures locale and time zone at first use: a hidden input, so a behavior change for review |

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

- **Hash iteration order changes per process,** and two equal sets can iterate differently in the same process. Never return or iterate a `Set`/`Dictionary` where order is observable. Hashing is seeded per process unless `SWIFT_DETERMINISTIC_HASHING` is set, which also removes hash-flooding resistance; a custom `hash(into:)` that hashes only part of the key weakens it the same way (`techniques/hostile-inputs.md`).
- **`Dictionary(uniqueKeysWithValues:)` crashes on a duplicate key,** where the `first(where:)` search it replaces returned the first match. `Dictionary(_:uniquingKeysWith:)` keeps the value you choose.
- **Slices keep their base's indices.** `arr[1...]` starts at index 1, so `slice[0]` crashes. Replacing `Array(arr[1...])` with the slice to avoid a copy changes every subscript into it; use `startIndex` or `first`. `Data` slices and `Substring` behave the same way.
- **Arithmetic overflow traps** in debug and release builds. A closed form or a different summation order can crash where the original did not. `Int` is 32 bits on watchOS (arm64_32), 32-bit Linux boards, and many embedded targets, so a formula safe on a 64-bit build can trap there. Converting `Double` to `Int`, or narrowing `Int` to `Int32` to save memory, traps when out of range.
- **`-Ounchecked` removes overflow and precondition checks.** Enabling it changes behavior on every input that used to trap: never a free speedup.
- **Sorts are stable.** `sort()` and `sorted()` are guaranteed stable. A predicate that is not a strict weak ordering (for example `<` on doubles containing NaN) gives an unspecified order, so a different algorithm can give a different result.
- **Strings compare by canonical equivalence.** `"é" == "e\u{301}"` is true, and `count` counts grapheme clusters. Switching keys or comparisons to `utf8`, `unicodeScalars`, or `[UInt8]` for speed changes equality, deduplication, and lengths for non-ASCII text.
- **NaN in hashed collections.** `NaN != NaN`, so a `Set<Double>` can hold several NaNs and never finds one, consistent with a `==` loop.
- **Value versus reference semantics.** Arrays, dictionaries, sets, and strings are values. Replacing them with a class-based structure introduces shared mutation.
- **Lazy sequences** run closures on demand and may run them again on each iteration.
- **`Equatable` versus `Hashable` consistency.** Custom types whose `==` and `hash(into:)` disagree break in sets and dictionaries.
- **Concurrency.** Moving to `async let` or task groups changes ordering, error, and cancellation behavior; actor isolation changes threading. Actor state can change across every `await` (reentrancy), so reordering or batching awaits inside an actor can break its invariants. Ask first.
- **Stack depth.** Secondary threads, concurrency tasks, and embedded targets have small stacks. A recursion that overflows on accepted input is a bug (rule 4).
- **Embedded Swift** supports only class-bound existentials before Swift 6.4 (full `any` arrives in 6.4), has no reflection, and possibly no heap allocation or Foundation. Techniques that need them are not candidates there; memory budgets are hard limits (rule 1).

## Testing, profiling, and benchmarking

- **Tests:** XCTest and Swift Testing (`@Test`, `#expect`, Swift 6+). `@Test(arguments:)` runs a test over every element of a collection, which makes exhaustive small-domain checks (level 3) cheap.
- **Property-based testing, if already present:** SwiftCheck (largely unmaintained). Otherwise a seeded generator (for example SplitMix conforming to `RandomNumberGenerator`) so cases reproduce.
- **Profiling:** Instruments (Time Profiler, Allocations) on Apple platforms; `perf` with `swift demangle`, Valgrind callgrind, or heaptrack on Linux. Profile optimized builds.
- **Benchmarks:** the `package-benchmark` package if already present (a dependency otherwise), or XCTest `measure { }`, in release builds; debug builds are dramatically slower and misleading. Foundation's performance differs between platforms: measure on the deployment OS.
- **Verification beyond tests** (see "Verification levels" in `DIFFERENTIAL-TESTING.md`): Thread Sanitizer (`-sanitize=thread`) and Address Sanitizer; the Swift 6 language mode's complete concurrency checking, which rejects data races at compile time. No mainstream bounded model checker targets Swift: reach level 3 by enumerating small domains exhaustively in tests.
- **Constant-time comparison** (for secrets; see `techniques/hostile-inputs.md`): message-authentication-code and digest types from CryptoKit (Apple platforms) or `swift-crypto` (elsewhere; a dependency) compare in constant time with `==`; raw byte arrays do not, so compare those with a loop that combines every byte difference without exiting early.

## References

Sources for the claims in this file are in `references/languages/SWIFT.md`. Read them only to verify a claim.
