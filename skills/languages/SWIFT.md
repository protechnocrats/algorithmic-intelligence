# Swift

Covers every Swift target, including Linux, Windows, WebAssembly, and Embedded Swift. Record the Swift version, the target, and the optimization mode: several APIs below need Swift 5.9 or 6.2, and `Int` is 32 bits on some targets (traps).

**Contents:** Built-in structures · Hidden costs · Bit manipulation · Swift-specific traps · Testing, profiling, and benchmarking · References

## Built-in structures

| Structure | Swift API | Key costs | Notes |
|---|---|---|---|
| Dynamic array | `Array` | subscript O(1), `append` amortized O(1), `insert(at: 0)`/`removeFirst()` O(n), `contains` O(n) | Value type, copy-on-write |
| Slice | `ArraySlice`, `Substring` | O(1) to create | Shares storage and keeps the whole base alive; indices are not zero-based |
| Hash set / map | `Set`, `Dictionary` | O(1) expected | Unordered; seeded per process |
| Flag set | `OptionSet` | O(1) on a raw integer | Idiomatic bitmask |
| String | `String` | `count` O(n); index offsetting O(n) | `String.Index`; iterates grapheme clusters |
| Contiguous storage | `ContiguousArray` | Like `Array`, no Objective-C bridging | Matters only on Apple platforms with class elements |
| Fixed-size inline array | `InlineArray<N, T>` (Swift 6.2+; on Apple platforms also an OS 26 deployment target, not back-deployed) | O(1), no heap allocation | Small buffers, embedded |
| Borrowed view | `Span`, `MutableSpan` (6.2+) | O(1), no copy or refcounting | Safe replacement for `withUnsafeBufferPointer` |
| Unique ownership | `~Copyable`, `borrowing`/`consuming` (5.9+) | No implicit copies or copy-on-write checks | Changes how callers use the type: a contract change (rule 11) |
| Lazy pipeline | `.lazy` | No intermediate arrays | Changes evaluation order |

### Not in the standard library

Deque, heap, ordered set and dictionary, bitset, and sorted collections. Apple's `swift-collections` package (a dependency) has `Deque`, `Heap`, `OrderedSet`, `OrderedDictionary`, `BitSet`, `BitArray`, `TreeSet`/`TreeDictionary` (persistent hash tries with cheap copies), and fixed-capacity `RigidArray`; its `SortedSet` and `SortedDictionary` are an unstable preview. Without it: a queue is an array plus a head index, compacted occasionally; a heap is a small in-project binary heap; an ordered set is an `Array` for order plus a `Set` for membership.

## Hidden costs

| Pattern | Cost | Fix |
|---|---|---|
| `removeFirst()` or `insert(_, at: 0)` in a loop | O(n²) total | Head index, reversed array with `popLast()`, or `Deque` |
| `contains(x)` or `firstIndex(of:)` in a loop | O(n·m) | `Set` or `Dictionary` once (traps: duplicate keys, string equality) |
| `var a = dict[k] ?? []; a.append(x); dict[k] = a` | Copies the array each update: O(n²) | `dict[k, default: []].append(x)` |
| `s[s.index(s.startIndex, offsetBy: i)]` in a loop | O(n²) | Iterate directly, `Array(s)` once, or `s.utf8` when semantics allow |
| `string.count` in a loop condition | O(n) each time | Compute once |
| Mutating a value also referenced elsewhere | Copy-on-write makes a full copy | Keep ownership unique; mutate in place with `inout`, not through a local `var` copy |
| Arrays or large structs mutated through a computed property | A copy per mutation | Mutate the stored property |
| `reduce([]) { $0 + [$1] }`, `reduce("") { $0 + $1 }` | O(n²) | `reduce(into:)`, `append`, `joined()` |
| `reserveCapacity(count + k)` on each call or batch | Reserves exactly what is asked, so growth turns linear: O(n²) overall; on bridged storage it always copies | Drop it, reserve once with the final size, or compute a geometric size |
| `filter { }.count`, `filter { }.first` | Allocates an array | `count(where:)` (6+), `first(where:)`, `contains(where:)` |
| `sorted()` in a loop | O(n log n) per iteration | Sort once, or a heap |
| `any Protocol` or unspecialized generics in a hot loop | Dynamic dispatch, boxing, no inlining | Generics or `some Protocol`; cross-module specialization needs `@inlinable`, an ABI change |
| Class instances in hot loops | Retain/release per access; copying a struct retains each class reference it holds | Structs, `final` or `private` classes, fewer references |
| Regex, formatter, or `JSONDecoder` built in a loop | Expensive initialization | Create once. A global or `static let` is lazy and thread-safe, but a shared formatter captures locale and time zone at first use: a behavior change |

### Input handling and security

- **Number parsing.** `Int(_: String)` accepts ASCII digits with an optional sign only and returns `nil` on whitespace or overflow; `Double(_: String)` also accepts `nan`, `inf`, and hex floats. `NumberFormatter`, `Decimal(string:)`, and `FormatStyle` follow the locale (`"1,5"`). `Character.isNumber` is true for non-ASCII digits and fractions.
- **Regex backtracks** (`Regex` and `NSRegularExpression`). Escape input with `NSRegularExpression.escapedPattern(for:)`.
- **Locale and time zone.** `uppercased()`/`lowercased()` ignore the locale; `localizedCaseInsensitiveCompare`, `localizedStandardCompare`, and formatters use it. A fixed-format `DateFormatter` needs `Locale(identifier: "en_US_POSIX")`. `Calendar.current` and `TimeZone.current` are hidden inputs to any cache.
- **Unsafe decoding.** `NSKeyedUnarchiver` without secure coding can instantiate arbitrary classes.

## Bit manipulation

| Operation | Swift |
|---|---|
| And, or, xor, not, shifts | `&`, `\|`, `^`, `~`, `<<`, `>>` |
| Popcount, trailing / leading zeros | `nonzeroBitCount`, `trailingZeroBitCount`, `leadingZeroBitCount` |
| Wrapping arithmetic | `&+`, `&-`, `&*`, `&<<` |
| Flags | `struct Flags: OptionSet { let rawValue: UInt64 }` |

`<<` and `>>` are "smart shifts": overshifting gives 0 (or -1 for negative values with `>>`) rather than wrapping; `&<<` and `&>>` mask the count.

## Swift-specific traps

- **Hash order changes per process,** and two equal sets can iterate differently in one process. Hashing is seeded unless `SWIFT_DETERMINISTIC_HASHING` is set, which also removes flooding resistance; a `hash(into:)` that hashes only part of the key weakens it the same way.
- **`Dictionary(uniqueKeysWithValues:)` crashes on a duplicate key,** where a `first(where:)` search returned the first match; `Dictionary(_:uniquingKeysWith:)` keeps the value you choose.
- **Slices keep their base's indices:** `arr[1...]` starts at 1, so `slice[0]` crashes. Replacing `Array(arr[1...])` with the slice changes every subscript into it. `Data` slices and `Substring` behave the same.
- **Overflow traps** in debug and release. `Int` is 32 bits on watchOS (arm64_32), 32-bit Linux boards, and many embedded targets, so a formula safe on 64-bit can trap there. `Double` to `Int` and narrowing to `Int32` trap when out of range.
- **`-Ounchecked`** removes overflow and precondition checks, changing behavior on every input that used to trap.
- **Sorts are stable;** a predicate that is not a strict weak ordering (`<` on doubles with NaN) gives an unspecified order.
- **Strings compare by canonical equivalence:** `"é" == "e\u{301}"`, and `count` counts grapheme clusters. Switching to `utf8`, `unicodeScalars`, or `[UInt8]` for speed changes equality, deduplication, and lengths for non-ASCII text.
- **NaN in hashed collections:** a `Set<Double>` can hold several NaNs and never finds one, consistent with a `==` loop.
- **Value semantics.** Collections and strings are values; a class-based replacement introduces shared mutation.
- **Lazy sequences** may run closures again on each iteration.
- **`==` and `hash(into:)` must agree** for custom types in sets and dictionaries.
- **Actor reentrancy.** Actor state can change across every `await`, so reordering or batching awaits inside an actor can break its invariants; `async let` and task groups change ordering, errors, and cancellation.
- **Stack depth.** Secondary threads, tasks, and embedded targets have small stacks.
- **Exclusivity.** In-place mutation or `inout` while another access to the same variable is live traps at runtime ("simultaneous accesses").
- **Embedded Swift** supports only class-bound existentials (`[unverified]` which version lifts this; check the Embedded Swift status page), has no reflection, and may lack heap allocation or Foundation. Memory budgets there are hard limits (rule 1).

## Testing, profiling, and benchmarking

- **Tests:** XCTest and Swift Testing (`@Test`, `#expect`, Swift 6+); `@Test(arguments:)` makes exhaustive small-domain checks (level 3) cheap. `Package.swift` runs when packages resolve; SwiftPM build-tool plugins and macros from dependencies run during the build; Xcode run-script phases run shell commands.
- **Property-based testing, if already present:** SwiftCheck (largely unmaintained); otherwise a seeded generator (SplitMix conforming to `RandomNumberGenerator`).
- **Profiling:** Instruments (Time Profiler, Allocations); on Linux `perf` with `swift demangle`, callgrind, or heaptrack. Profile optimized builds.
- **Benchmarks:** `package-benchmark` if present, or XCTest `measure { }`, in release builds (debug builds are dramatically slower). Foundation performance differs between platforms: measure on the deployment OS.
- **Verification beyond tests** ("Verification levels" in `DIFFERENTIAL-TESTING.md`): Thread and Address Sanitizers; Swift 6 mode's complete concurrency checking rejects data races at compile time. No mainstream bounded model checker targets Swift.
- **Constant-time comparison:** CryptoKit (or `swift-crypto`, a dependency) MAC and digest types compare in constant time with `==`; raw byte arrays do not, so compare those with a loop that combines every byte difference without exiting early.

## References

Sources: `references/languages/SWIFT.md`.
