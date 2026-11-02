# C#

Load this file for C# projects. Record the target framework and runtime: several structures below need .NET 5, 6, or 8, and runtimes other than .NET (Mono, IL2CPP) differ in garbage collection and in which APIs exist.

## Built-in structures

| Structure | API | Key costs | Notes |
|---|---|---|---|
| Dynamic array | `List<T>` | index O(1), `Add` amortized O(1), `Insert(0, x)`/`RemoveAt(0)` O(n), `Contains`/`IndexOf`/`Remove(item)` O(n) | |
| Hash map / set | `Dictionary<K,V>`, `HashSet<T>` | O(1) average | Enumeration order is unspecified |
| Sorted map | `SortedDictionary<K,V>` | O(log n) insert, remove, lookup | Red-black tree |
| Sorted list | `SortedList<K,V>` | O(log n) lookup, **O(n) insert and remove** | Array-backed; good only for mostly-read data |
| Sorted set | `SortedSet<T>` | O(log n); `GetViewBetween`, `Min`, `Max` | |
| Queue / stack | `Queue<T>`, `Stack<T>` | O(1) amortized | |
| Linked list | `LinkedList<T>` | O(1) insert/remove with a node reference; O(n) search | |
| Priority queue | `PriorityQueue<TElement, TPriority>` (.NET 6+) | Enqueue/Dequeue O(log n) | No priority update; not stable for equal priorities |
| Bitset | `BitArray` | O(1) per bit, O(n/32) bulk ops | |
| Flags | `[Flags] enum` | O(1) bit ops | `HasFlag` is fast on modern .NET |
| Read-optimized | `FrozenDictionary`, `FrozenSet` (.NET 8+) | Faster lookups, slower creation | For data built once and read many times |
| Immutable | `ImmutableArray<T>`, `ImmutableList<T>`, `ImmutableDictionary` | **`ImmutableList` index access is O(log n)** (it is a tree) | `ImmutableArray` is O(1) index |
| Concurrent | `ConcurrentDictionary`, `ConcurrentQueue`, `Channel<T>` | O(1) average | Keep thread-safety when replacing |
| Low-allocation | `Span<T>`, `Memory<T>`, `ArrayPool<T>`, `stackalloc`, `StringBuilder` | Avoid copies and allocations | |

Not in the base library: deque, interval tree, trie, multimap. Ask before adding a package (rule 7).

## Hidden costs

| Pattern | Cost | Fix |
|---|---|---|
| Enumerating the same `IEnumerable<T>` query more than once | Re-runs the whole query each time (possibly a database query) | Materialize once with `ToList()`/`ToArray()` (check deferred-execution trap) |
| `.Count()` on an `IEnumerable<T>` that is not an `ICollection` | O(n) | `.Count` property on collections; `Any()` for emptiness |
| `ElementAt(i)` inside a loop over an `IEnumerable` | O(n²) | Materialize to a list or array |
| `list.Contains(x)` inside `Where` | O(n·m) | `HashSet<T>` built once |
| `list.First(x => x.Id == id)` inside a loop | O(n·m) | `ToDictionary(x => x.Id)` once (throws on duplicate keys, see traps) |
| `OrderBy` inside a loop | O(n log n) per iteration | Sort once |
| `list.Remove(item)` or `RemoveAt(0)` in a loop | O(n²) | `RemoveAll(predicate)`, `Queue<T>`, or build a new list |
| `string +=` in a loop | O(n²) | `StringBuilder` or `string.Join` |
| `new Regex(...)` in hot code | Recompiles | `static readonly Regex` or `[GeneratedRegex]` (.NET 7+) |
| `ContainsKey` followed by indexer | Two lookups | `TryGetValue`; `CollectionsMarshal.GetValueRefOrAddDefault` (.NET 6+) |
| Non-generic `ArrayList`, `Hashtable` with value types | Boxing | Generic collections |
| Exceptions used for control flow in hot loops | Very expensive throws | `TryParse`/`TryGetValue` patterns |
| Lambdas capturing variables in hot loops | Closure allocations | Static lambdas or plain loops, only when measured |

## Bit manipulation

| Operation | C# |
|---|---|
| And, or, xor, not, shifts | `&`, `\|`, `^`, `~`, `<<`, `>>`, `>>>` (C# 11+, unsigned right shift) |
| Popcount | `BitOperations.PopCount(x)` (.NET Core 3.0+), `int.PopCount` (.NET 7+) |
| Trailing / leading zeros | `BitOperations.TrailingZeroCount`, `BitOperations.LeadingZeroCount` |
| Power of two | `BitOperations.IsPow2` (.NET 6+) |
| Flags | `[Flags] enum Permissions : long { ... }` |

Shift counts are masked to 5 bits for `int` and 6 bits for `long`.

## C#-specific traps

- **Sort stability:** LINQ `OrderBy`/`ThenBy` are **stable**; `List<T>.Sort` and `Array.Sort` are **unstable** (introsort). Replacing `OrderBy` with `List.Sort` to avoid allocation changes the order of equal elements.
- **Dictionary enumeration order** is unspecified. In practice it often looks like insertion order until removals occur, so tests may pass by accident.
- **`Add` versus indexer:** `dict.Add(k, v)` and `ToDictionary` throw on duplicate keys; `dict[k] = v` overwrites; a `First()` search returned the first match.
- **Deferred execution:** LINQ queries run when enumerated. Materializing a query earlier (or later) changes which data it sees if the source changes in between, and when exceptions surface.
- **Comparers:** dictionaries and sets with `StringComparer.OrdinalIgnoreCase` or culture-specific comparers behave differently from the default. Keep the same comparer.
- **Struct copies:** mutating a struct obtained from a list indexer or a property mutates a copy.
- **Overflow:** arithmetic is unchecked by default and wraps silently, unless the project enables `CheckForOverflowUnderflow` or uses `checked` blocks.
- **`PriorityQueue` order for equal priorities** is not FIFO.
- **Nullability:** `Dictionary` rejects `null` keys; nullable reference type annotations are compile-time only.

## Testing and benchmarking

- **Tests:** xUnit, NUnit, MSTest.
- **Property-based testing, if already present:** FsCheck, CsCheck.
- **Profiling:** `dotnet-trace` and `dotnet-counters` (cross-platform CLI tools; installs), PerfView on Windows, or the Visual Studio / Rider profilers.
- **Benchmarks, if already present:** BenchmarkDotNet (a dependency otherwise; ask), with `[MemoryDiagnoser]` for allocations. Use Release builds. Without it, use `Stopwatch` with warmup and medians in test code.
- **Verification beyond tests** (see "Verification levels" in `DIFFERENTIAL-TESTING.md`; ask unless present): Coyote for systematic testing of concurrent and asynchronous code, which explores interleavings and replays failures; Dafny for proofs, compiling verified code to C#.
- **Constant-time comparison** (for secrets; see `techniques/hostile-inputs.md`): `CryptographicOperations.FixedTimeEquals`, never `SequenceEqual` on secrets.

## References (for verifying claims; not required reading)

- .NET collections: learn.microsoft.com/en-us/dotnet/standard/collections/; API: learn.microsoft.com/en-us/dotnet/api/system.collections.generic
