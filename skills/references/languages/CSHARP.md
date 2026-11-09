# References for `languages/CSHARP.md`

Sources for the claims in `languages/CSHARP.md`. Read only to verify a claim, on the page for the project's language and library version.

- .NET collections: learn.microsoft.com/en-us/dotnet/standard/collections/; API: learn.microsoft.com/en-us/dotnet/api/system.collections.generic
- `OrderBy` computing keys once: src/libraries/System.Linq/src/System/Linq/OrderedEnumerable.cs in github.com/dotnet/runtime (implementation behavior). `List<T>.GetRange`, `List<T>.Sort`, `record` hashing, friend assemblies: learn.microsoft.com/dotnet.
- `PriorityQueue<TElement,TPriority>.Remove`, a linear scan: learn.microsoft.com/dotnet/api/system.collections.generic.priorityqueue-2.remove (its version list starts at .NET 9) and src/libraries/System.Collections/src/System/Collections/Generic/PriorityQueue.cs in github.com/dotnet/runtime.
- Packages: github.com/morelinq/MoreLINQ; github.com/bitfaster/BitFaster.Caching; learn.microsoft.com/aspnet/core/performance/caching/memory (`MemoryCache` compaction order and `SizeLimit`); deprecation and release data from nuget.org.
