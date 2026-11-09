# C#

Record the target framework and runtime: several APIs below name the .NET version they need, and Mono and IL2CPP differ in garbage collection and available APIs.

**Contents:** Built-in structures · Hidden costs · Bit manipulation · C#-specific traps · Testing and benchmarking · References

## Built-in structures

| Structure | API | Key costs | Notes |
|---|---|---|---|
| Dynamic array | `List<T>` | index O(1), `Add` amortized O(1), `Insert(0, x)`/`RemoveAt(0)` O(n), `Contains`/`IndexOf`/`Remove(item)` O(n) | `BinarySearch` on sorted data, as on arrays |
| Hash map / set | `Dictionary<K,V>`, `HashSet<T>` | O(1) average | Enumeration order unspecified |
| Sorted map | `SortedDictionary<K,V>` | O(log n) | Red-black tree. No floor, ceiling, range, `Min`, or `Max` of its own: use `SortedSet<T>` for those |
| Sorted list | `SortedList<K,V>` | O(log n) lookup, O(n) insert and remove | Array-backed; for mostly-read data |
| Sorted set | `SortedSet<T>` | O(log n); `GetViewBetween`, `Min`, `Max` | |
| Queue / stack | `Queue<T>`, `Stack<T>` | O(1) amortized | |
| Linked list | `LinkedList<T>` | O(1) insert/remove at a node; O(n) search | |
| Priority queue | `PriorityQueue<TElement, TPriority>` (.NET 6+) | O(log n) | No in-place priority update; re-prioritize by lazy deletion. `Remove` (.NET 9+) is a linear scan, and which of several equal elements it removes is not deterministic. Equal priorities not FIFO |
| Bitset | `BitArray` | O(1) per bit, O(n/32) bulk | |
| Read-optimized | `FrozenDictionary`, `FrozenSet` (.NET 8+) | Faster lookups, slower creation | Built once, read many times |
| Immutable | `ImmutableArray<T>`, `ImmutableList<T>`, `ImmutableDictionary` | `ImmutableList` index is O(log n) (a tree); `ImmutableArray` is O(1) | |
| Concurrent | `ConcurrentDictionary`, `ConcurrentQueue`, `Channel<T>` | O(1) average | Keep thread-safety when replacing |
| Low-allocation | `Span<T>`, `Memory<T>`, `ArrayPool<T>`, `stackalloc`, `StringBuilder` | Avoid copies and allocations | See traps |

Not in the base library: deque, interval tree, trie, multimap, bounded LRU cache, sorted multiset.

### Packages

These are dependencies (rule 7): check the module's manifest first, and follow "When the best technique is not available" in `ALGORITHM-ARSENAL.md`.

| Package | Provides | Watch for |
|---|---|---|
| `morelinq` | `PartialSort`, `PartialSortBy` (top-k), `DistinctBy` | Stability is not stated: test ties against the original |
| `BitFaster.Caching` | `ConcurrentLru`, `ConcurrentLfu` | Both are approximate: `ConcurrentLru` is a pseudo-LRU on the 2Q policy, so eviction differs from a strict LRU |
| `Microsoft.Extensions.Caching.Memory` | `MemoryCache` | Not an LRU: it compacts by expiry and priority before recency. With `SizeLimit` every entry must set a size, and an entry that would exceed the limit is not cached. `GetOrCreate` is not atomic. Expiration is not done in the background |

`Microsoft.Experimental.Collections` (`MultiValueDictionary`) is deprecated; for a multimap use `Dictionary<K, List<V>>`. No maintained deque package was verified: write a ring buffer in the project with tests.

## Hidden costs

| Pattern | Cost | Fix |
|---|---|---|
| Enumerating one `IEnumerable<T>` query more than once | Re-runs the query each time (possibly a database query) | Materialize once with `ToList()` |
| `.Count()` on an `IEnumerable<T>` that is not an `ICollection` | O(n) | `.Count` on collections; `Any()` for emptiness |
| `ElementAt(i)` in a loop over an `IEnumerable` | O(n²) | Materialize |
| `list.Contains(x)` inside `Where`; `First(x => x.Id == id)` in a loop | O(n·m) | `HashSet<T>` or `ToDictionary` once (throws on duplicate keys) |
| `OrderBy` inside a loop | O(n log n) per iteration | Sort once |
| `list.Sort((a, b) => Parse(a).CompareTo(Parse(b)))` | `Parse` runs inside every comparison | Compute keys first, then `Array.Sort(keys, items)`. LINQ `OrderBy` computes each key once before sorting (dotnet/runtime behavior, not documented), but it is stable where `List.Sort` is not, so moving between them changes ties |
| `list.GetRange(1, n)` in recursion | Copies each call: O(n²) | Pass indices, or `Span<T>.Slice` |
| A `record` with many members as a `Dictionary` key | Its `GetHashCode` combines every member | A small ID or a narrower key type |
| `Remove(item)` or `RemoveAt(0)` in a loop | O(n²) | `RemoveAll(predicate)`, `Queue<T>`, or a new list |
| `string +=` in a loop | O(n²) | `StringBuilder`, `string.Join` |
| `new Regex(...)` in hot code | Recompiles | `static readonly Regex` or `[GeneratedRegex]` (.NET 7+) |
| `ContainsKey` then indexer | Two lookups | `TryGetValue`; `CollectionsMarshal.GetValueRefOrAddDefault` (.NET 6+) |
| `ArrayList`, `Hashtable` with value types | Boxing | Generic collections |
| Exceptions as control flow in hot loops | Very expensive throws | `TryParse`/`TryGetValue` |
| A `struct` key without `IEquatable<T>` and `GetHashCode` | Default `ValueType.Equals` boxes and uses reflection | Implement both, or use a `record struct` |

### Input handling and security

- **Parsing and formatting use the current culture** unless given one. `int.Parse` accepts surrounding whitespace and a culture-specific sign; `double.Parse("1,5")` is 1.5 in `de-DE` and 15 in `en-US`; `ToString()` writes the culture's separators. A faster parser (`Utf8Parser`, spans) keeps the same culture and `NumberStyles`; new code passes `CultureInfo.InvariantCulture`.
- **Culture-sensitive strings.** `ToUpper()`, `ToLower()`, `string.Compare`, `StartsWith(string)`, and `IndexOf(string)` use the current culture (Turkish `i`; ICU-based on .NET 5+). Switching to `StringComparison.Ordinal` for speed changes non-ASCII results.
- **`Regex` backtracks by default.** Keep any match timeout. `RegexOptions.NonBacktracking` (.NET 7+) is linear but drops backreferences and lookarounds and can capture differently. Escape input with `Regex.Escape`.
- **Hashing.** `string.GetHashCode` is randomized per process on .NET Core and .NET 5+, not on .NET Framework; `int` and most value types hash to fixed values, so chosen keys collide: worst case O(n) per lookup.
- **Stack and deserialization.** `StackOverflowException` cannot be caught and ends the process. `BinaryFormatter`, and Json.NET with `TypeNameHandling` other than `None`, run code from data.

## Bit manipulation

| Operation | C# |
|---|---|
| And, or, xor, not, shifts | `&`, `\|`, `^`, `~`, `<<`, `>>`, `>>>` (C# 11+, unsigned) |
| Popcount | `BitOperations.PopCount` (.NET Core 3.0+), `int.PopCount` (.NET 7+) |
| Trailing / leading zeros | `BitOperations.TrailingZeroCount`, `LeadingZeroCount` |
| Power of two | `BitOperations.IsPow2` (.NET 6+) |
| Flags | `[Flags] enum Permissions : long`; `HasFlag` is fast on modern .NET |

Shift counts are masked to 5 bits for `int` and 6 bits for `long`.

## C#-specific traps

- **Sort stability:** LINQ `OrderBy`/`ThenBy` are stable; `List<T>.Sort` and `Array.Sort` are not (introsort). Replacing `OrderBy` with `List.Sort` to save allocation reorders equal elements.
- **Dictionary order** is unspecified but looks like insertion order until removals occur, so tests can pass by accident.
- **Duplicates:** `Add` and `ToDictionary` throw on a duplicate key; `dict[k] = v` overwrites; a `First()` search returned the first match.
- **Deferred execution:** materializing a query earlier or later changes what data it sees and when exceptions surface.
- **Comparers:** keep the original's (`StringComparer.OrdinalIgnoreCase`, culture comparers).
- **Struct copies:** mutating a struct from a list indexer or property mutates a copy.
- **Overflow:** arithmetic wraps silently unless `CheckForOverflowUnderflow` or `checked` is used, but `Enumerable.Sum` and `Average` on integers are checked and throw `OverflowException`; replacing one with a loop, or the reverse, changes overflow behavior.
- **`ArrayPool` and `stackalloc`.** A rented array can be longer than requested and keeps old contents unless returned with `clearArray: true`: use only the requested length, and clear sensitive data. `stackalloc` sized from input overflows the stack uncatchably: cap it and fall back to the heap.
- **Nullability:** `Dictionary` rejects `null` keys; nullable annotations are compile-time only.

## Testing and benchmarking

- **Tests:** xUnit, NUnit, MSTest. `dotnet build` and `dotnet test` run MSBuild targets from project files, `Directory.Build.props`/`.targets` in any parent directory, and NuGet packages, plus source generators and analyzers.
- **Testing an extracted function:** `internal`, with `InternalsVisibleTo` naming the test assembly.
- **Property-based testing, if already present:** FsCheck, CsCheck.
- **Profiling:** `dotnet-trace`, `dotnet-counters` (global tool installs), PerfView, or the Visual Studio / Rider profilers.
- **Benchmarks:** BenchmarkDotNet if already present, with `[MemoryDiagnoser]`; Release builds, no debugger. Otherwise `Stopwatch` with warmup long enough for tiered compilation to settle, medians, and results kept observable.
- **Verification beyond tests** ("Verification levels" in `DIFFERENTIAL-TESTING.md`): Coyote for concurrent and async code (explores interleavings, replays failures); Dafny, compiling verified code to C#.
- **Constant-time comparison:** `CryptographicOperations.FixedTimeEquals`. `SequenceEqual` stops at the first difference.

## References

Sources: `references/languages/CSHARP.md`.
