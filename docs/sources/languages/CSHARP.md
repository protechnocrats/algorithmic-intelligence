# Sources for `skills/languages/CSHARP.md`

Where each claim in that file comes from, for maintainers and reviewers. Not part of the installed skill. API pages are under learn.microsoft.com/dotnet/api/ followed by the lowercase type name (for example `system.collections.generic.sortedset-1`); the costs are in each page's Remarks.

## Built-in structures

- Costs of the collection types: "Collections and Data Structures," section "Algorithmic complexity of collections" (learn.microsoft.com/dotnet/standard/collections/).
- `SortedDictionary<TKey,TValue>` (a binary search tree, no `Min` or range API): `system.collections.generic.sorteddictionary-2`. `SortedList<TKey,TValue>` (array-backed, O(n) insert and remove): `system.collections.generic.sortedlist-2`. `SortedSet<T>` (`GetViewBetween`, `Min`, `Max`): `system.collections.generic.sortedset-1`.
- `PriorityQueue<TElement,TPriority>` (no FIFO order for equal priorities): `system.collections.generic.priorityqueue-2`. `Remove`, a linear scan, .NET 9 and later: `system.collections.generic.priorityqueue-2.remove` and src/libraries/System.Collections/src/System/Collections/Generic/PriorityQueue.cs in github.com/dotnet/runtime.
- `BitArray`: `system.collections.bitarray`. `FrozenDictionary`, `FrozenSet` (.NET 8): `system.collections.frozen.frozendictionary-2`.
- `ImmutableList<T>` as a tree with O(log n) indexing: `system.collections.immutable.immutablelist-1` and "Immutable collections" guidance at learn.microsoft.com/dotnet/api/system.collections.immutable.
- `ArrayPool<T>.Rent` returning an array at least as long as requested: `system.buffers.arraypool-1.rent`; `Return` with `clearArray`: `system.buffers.arraypool-1.return`.

## Packages

- MoreLINQ `PartialSort`, `PartialSortBy`, `DistinctBy`: github.com/morelinq/MoreLINQ (README method list) and morelinq.github.io reference pages. `Enumerable.DistinctBy` (.NET 6 and later): `system.linq.enumerable.distinctby`; the CS0121 ambiguity when both are in scope: C# compiler error CS0121 at learn.microsoft.com/dotnet/csharp/misc/cs0121.
- BitFaster.Caching `ConcurrentLru` (pseudo-LRU on 2Q) and `ConcurrentLfu`: github.com/bitfaster/BitFaster.Caching, README and wiki pages for each cache.
- `MemoryCache` compaction order, `SizeLimit`, `GetOrCreate` not atomic, no background expiration: "Caching in-memory in ASP.NET Core" (learn.microsoft.com/aspnet/core/performance/caching/memory), sections "Use SetSize, Size, and SizeLimit to limit cache size" and "Cache guidelines".
- `MultiValueDictionary` deprecation: the `Microsoft.Experimental.Collections` package page on nuget.org.

## Hidden costs

- `OrderBy` computing each key once before sorting: src/libraries/System.Linq/src/System/Linq/OrderedEnumerable.cs in github.com/dotnet/runtime (implementation behavior, not documented). `List<T>.Sort` unstable: `system.collections.generic.list-1.sort` ("This method performs an unstable sort"); `Enumerable.OrderBy` stable: `system.linq.enumerable.orderby` ("This method performs a stable sort").
- `List<T>.GetRange` copying: `system.collections.generic.list-1.getrange`. `ToDictionary` throwing on duplicate keys: `system.linq.enumerable.todictionary`.
- `record` equality and hashing over every member: "Records" in the C# reference (learn.microsoft.com/dotnet/csharp/language-reference/builtin-types/record), section "Value equality".
- Default `ValueType.Equals` (reflection) and `ValueType.GetHashCode` (may use only the first field): Remarks on `system.valuetype.equals` and `system.valuetype.gethashcode`.
- `Regex` construction cost and source generation (.NET 7): "Regular expression source generators" and "Best practices for regular expressions in .NET" (learn.microsoft.com/dotnet/standard/base-types/).
- `CollectionsMarshal.GetValueRefOrAddDefault`: `system.runtime.interopservices.collectionsmarshal.getvaluereforadddefault`.

## Input handling and security

- `int.Parse` styles and culture: `system.int32.parse` and `system.globalization.numberstyles` (`NumberStyles.Integer`, `NumberStyles.Float | AllowThousands`).
- Culture-sensitive string operations and `StringComparison.Ordinal`: "Best practices for comparing strings in .NET" (learn.microsoft.com/dotnet/standard/base-types/best-practices-strings). ICU on .NET 5 and later: "Globalization and ICU" (learn.microsoft.com/dotnet/core/extensions/globalization-icu).
- Backtracking, match timeouts, and `RegexOptions.NonBacktracking` (.NET 7) and what it does not support: "Backtracking in regular expressions" and "Regular expression options" (learn.microsoft.com/dotnet/standard/base-types/).
- `string.GetHashCode` randomized per process on .NET Core: Remarks on `system.string.gethashcode`.
- `StackOverflowException` cannot be caught: Remarks on `system.stackoverflowexception`. `BinaryFormatter`: "BinaryFormatter security guide" (learn.microsoft.com/dotnet/standard/serialization/binaryformatter-security-guide). Json.NET `TypeNameHandling`: www.newtonsoft.com/json/help/html/T_Newtonsoft_Json_TypeNameHandling.htm (its security note).

## Bit manipulation and traps

- `BitOperations` (`PopCount`, `TrailingZeroCount`, `LeadingZeroCount`, `IsPow2`): `system.numerics.bitoperations`. `int.PopCount` (.NET 7): `system.int32.popcount`.
- `>>>` (C# 11) and shift-count masking: C# reference, "Bitwise and shift operators" (learn.microsoft.com/dotnet/csharp/language-reference/operators/bitwise-and-shift-operators).
- `checked` arithmetic and `CheckForOverflowUnderflow`: C# reference, "The checked and unchecked statements" and compiler option "CheckForOverflowUnderflow". `Enumerable.Sum` throwing `OverflowException`: Exceptions section of `system.linq.enumerable.sum`.
- `Dictionary` enumeration order unspecified: Remarks on `system.collections.generic.dictionary-2`.
- `stackalloc`: C# reference, "stackalloc expression".

## Testing and benchmarking

- Friend assemblies and `InternalsVisibleTo`: learn.microsoft.com/dotnet/standard/assembly/friend.
- `Directory.Build.props` and `.targets` imported from parent directories: "Customize your build" (learn.microsoft.com/visualstudio/msbuild/customize-your-build).
- BenchmarkDotNet and `[MemoryDiagnoser]`: benchmarkdotnet.org/articles/configs/diagnosers.html. Tiered compilation: "Tiered compilation" in the .NET runtime configuration docs.
- Coyote: microsoft.github.io/coyote. Dafny's C# back end: dafny.org/latest/DafnyRef/DafnyRef ("Compilation to C#").
- `CryptographicOperations.FixedTimeEquals`: `system.security.cryptography.cryptographicoperations.fixedtimeequals`.
