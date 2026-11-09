# Algorithm Arsenal

How to find candidate approaches: triage questions, routing by current complexity, lower bounds, and reformulation. Check the structures already on the path first ([DATA-STRUCTURES.md](DATA-STRUCTURES.md)); a replacement found there is a candidate here. The technique tables are in [CORE-TECHNIQUES.md](CORE-TECHNIQUES.md); [ADVANCED-TECHNIQUES.md](ADVANCED-TECHNIQUES.md) routes specialized domains to the files under `techniques/`; [DISCOVERY.md](DISCOVERY.md) is for problems no row fits. The first technique that improves the bound is rarely the last one worth checking: look at every section whose signals match, and at combinations.

**Contents:** Start with six questions · Analyzing recursive code · Start from the current complexity · Lower bounds · Reformulate before choosing · Behavior-changing techniques · When the best technique is not available · References

## Start with six questions

1. **Is this work needed at all?** Output computed and then discarded, a value recomputed that a parameter, field, or earlier step already holds, a query whose result the caller already has. Avoiding work is often the largest win and the easiest way to break something, so it is a proposal under "Removing work" in "Rule details" in `WORKFLOW.md`, reported as "work avoided" rather than a complexity reduction. "Nothing changed, so skip the refresh" is a cache that needs invalidation, not removal.
2. **Am I repeating work?** Cache, memoize, hoist invariants, precompute ("Caching traps" in `BEHAVIOR-TRAPS.md`).
3. **Am I searching repeatedly?** Build an index, hash set, sorted structure, or lookup table. With attacker-chosen keys, keep the platform's randomized hashing or use a sorted structure (`techniques/hostile-inputs.md`).
4. **Am I keeping more information than I need?** Rolling state, a bounded heap, a streaming algorithm, a compact representation.
5. **Can I reorder or batch the work?** Sort offline, sweep, batch I/O, process independent work together.
6. **What assumptions make the faster algorithm valid?** Monotonicity, static versus changing data, value bounds, sign, ordering requirements, purity, memory limits. Most wrong optimizations are a technique used outside its "Valid when" column, so settle each condition from a check the code enforces or the code that builds the data, for every input the code accepts; a name, type, or comment saying "sorted" or "non-negative" is a claim. A combination inherits the conditions of every row it combines (the "Combinations" table in `techniques/sequences-dp-search.md` has no column of its own).

## Analyzing recursive code

Complexity is most often misjudged in recursive code. Write the recurrence from the code, then solve it:

- **Divide and conquer, T(n) = a·T(n/b) + f(n):** compare f(n) with n^(log_b a). If f grows polynomially slower, T(n) = Θ(n^(log_b a)). If they match up to a factor of log^k n with k ≥ 0, T(n) = Θ(n^(log_b a) · log^(k+1) n) (for k = −1 it is Θ(n^(log_b a) · log log n), and for k < −1 it is Θ(n^(log_b a))). If f grows polynomially faster (and a·f(n/b) ≤ c·f(n) for some c < 1), T(n) = Θ(f(n)). Example: T(n) = 2T(n/2) + n log n is Θ(n log² n), not Θ(n log n).
- **Uneven splits,** such as T(n) = T(n/3) + T(2n/3) + n: use Akra-Bazzi or sum the recursion tree level by level. This one is Θ(n log n).
- **Shrinking by a constant:** T(n − 1) + O(1) is O(n); T(n − 1) + O(n) is O(n²); 2T(n − 1) + O(1) is O(2ⁿ); T(n − 1) + T(n − 2) + O(1) is Θ(φⁿ), about 1.618ⁿ.
- **Memoized recursion** costs the number of distinct subproblems times the work per subproblem, whatever the recurrence.
- **Average case** needs a stated input distribution. Quicksort with a fixed pivot rule makes about 1.39 n log₂ n comparisons on average over random orders, and n²/2 on its worst inputs, which may be the common ones (already sorted data).

"Expected" averages over the algorithm's randomness or hashing; "amortized" averages over a sequence of operations. Neither is a worst-case guarantee. When unsure, sum the recursion tree and confirm with a doubling experiment (`BENCHMARKING.md`).

## Start from the current complexity

Find the row for the candidate's current cost along the whole call chain, not only inside the function body. Quoted section names are in `CORE-TECHNIQUES.md` unless a file is named.

| Current cost | Usual cause | Look first at |
|---|---|---|
| O(n!) | Trying every ordering or assignment | Polynomial scheduling and assignment cases in `techniques/optimization-and-scheduling.md`; bitmask DP ("Bit manipulation"); sorting by a key when an exchange argument shows the order is determined ("Reusing work", greedy) |
| O(cⁿ) | Recursion that branches over overlapping subproblems; trying every subset | Memoization, DP, knapsack DP ("Reusing work"); meet-in-the-middle, branch and bound, constraint propagation ("Combinatorial search" in `techniques/sequences-dp-search.md`). If NP-hard in general, check whether small integer weights or targets allow a pseudo-polynomial DP, or whether the input size keeps exact search affordable |
| O(n³) or higher polynomial | Triple-nested loops; a quadratic loop that calls a linear helper | Precompute what the innermost loop recomputes (prefix sums, a hash index); sort plus two pointers ("Combinations"); "Dynamic programming optimizations" in `techniques/sequences-dp-search.md` |
| O(n²) | Nested loops over related collections; a linear search or front removal inside a loop | "Lookup, membership, counting", "Order and search", "Structures for repeated queries", "Combinations" |
| A product of size variables (O(n·m), O(V·E)) | For each A, scan all B | "Invert the loop" under "Reformulate before choosing". The right fix depends on which variable is large |
| O(n log n) | A sort, or n heap or tree operations | Whether the order is observable at all; top-k, min, or max without a full sort ("Priority and selection"); non-comparison sorts for bounded keys |
| O(n) per call, called many times | Recomputing from scratch on every call | "Precompute once, query many times" and "Incremental maintenance" under "Reformulate before choosing"; "Structures for repeated queries"; "Changing graphs" in `techniques/graphs-and-trees.md` |
| O(n²) over objects in space | Every pair checked for distance, overlap, or collision; every ray against every object | `techniques/spatial-data.md`, `techniques/geometry-and-cad.md`, `techniques/games-and-simulation.md` |
| O(N·k²) over pixels or samples | A filter that visits every neighbor of every pixel or sample | `techniques/images-and-signals.md` |
| Model training or inference slower than expected | Recomputed attention, host and device synchronization, data loading, element-by-element loops over tensors | `techniques/machine-learning.md` |
| Latency high while each step's own work is small, or tail latency far above the median | Utilization near capacity, head-of-line blocking, fan-out, unbounded queues | `techniques/queues-and-latency.md` |
| Cost dominated by page or disk I/O, cache misses, branch misses, or cache hit rate | Data layout, storage structure, or eviction policy | "Storage and indexing" in `techniques/data-at-scale.md`, "Memory locality" in `techniques/hardware-and-concurrency.md`, "Caching and eviction" in `techniques/specialized-structures.md` |

## Lower bounds

A lower bound tells you when to stop. Each holds in a model (comparison-based, hashing, bounded integers); state the model with the bound.

- **Must read the input:** if the answer can depend on every element, Ω(n). Sublinear needs preprocessing or extra structure (sortedness, an index).
- **Comparison sorting:** Ω(n log n) worst case and on average over random orders. Adaptive sorts go below it only on inputs with measured structure (presorted runs, few distinct keys). Counting and radix sort beat it for bounded or fixed-width keys; bucket sort also needs a near-uniform distribution an attacker cannot break.
- **Search in unsorted data:** Ω(n) per query. For repeated queries, an O(n) index then O(1) expected per query.
- **Search in sorted data:** Θ(log n) by comparison. A hash index gives O(1) expected after O(n) preprocessing and space; it does not pay for a one-off query, must keep the original equality semantics, and has a worse worst case.
- **Output size:** k results cost Ω(k). Listing all pairs is Ω(n²) when there can be n² pairs.
- **No known faster algorithm:** nothing substantially below O(n²) is known for 3SUM and the problems that reduce to it, and nothing polynomial for NP-hard problems (0/1 knapsack, subset sum, traveling salesperson). Say the bound is conjectured.
- **Repeated calls:** for m calls on the same or slowly changing data, the cost is the total across calls; preprocessing once can beat any per-call algorithm.
- **No bound can be established:** costs dominated by a query plan, round trips, lock contention, cache behavior, or the data distribution often have none. Report "unknown" with the reason, give the strongest bound you can support ("one pass over the input", "one round trip per distinct key", "the size of the output"), and record which approaches you weighed, since you cannot prove you are done.

A bound in a comment or an earlier report ("already optimal") is a claim; derive it from one of the reasons above. If the chosen approach stays above the bound, the reason is one of: the better bound needs an unapproved dependency, exceeds a hard memory budget (give the numbers), would change something callers rely on, preprocessing the call pattern cannot amortize, an assumption the code does not satisfy, or constant factors that lose at realistic sizes (shown by a benchmark).

## Reformulate before choosing

Many large wins come from changing the problem rather than speeding up the loop. [DISCOVERY.md](DISCOVERY.md) has the method for deriving new reformulations.

- **Precompute once, query many times.** Build a map, prefix array, or sorted copy once. Valid only while the source does not change between queries; otherwise it is a cache and needs invalidation.
- **Invert the loop.** Instead of "for each A, scan all B", index B once and look up each A.
- **Count the complement.** Counting what fails can be cheaper than counting what passes.
- **Transform the key space.** Coordinate compression, normalized keys, sorting by one dimension to make another a sweep.
- **Offline processing.** If all queries are known up front and no answer is needed before later queries arrive, sort or batch them, then return answers in the original order.
- **Incremental maintenance.** Update a running result instead of recomputing. Every path that changes the data must update it, including direct database writes and other services; a missed path makes the result silently stale.
- **Process changes, not snapshots.** When the source reports what changed (replication log, change data capture, file-system notifications, an event stream), consume the changes; cost becomes proportional to the change. See "Change propagation" in `techniques/data-at-scale.md`.
- **Cheap check first.** An inexpensive test that can only rule candidates out (Bloom filter, per-block min and max, bounding box, length or hash comparison) before the exact check. It must never reject what the exact check would accept. Not on secrets: an early exit on a token, MAC, or password hash is a timing leak. With untrusted input, attackers can make everything pass the cheap check, so the bound is the slow path's.
- **Choose by the input.** When different implementations win on different inputs, pick per call from measured properties (size below a crossover, presorted runs, duplicates, density, key width, CPU features), as query planners, pdqsort, Timsort, size-class allocators, and `memcpy` do. Count the classification cost, measure crossovers (`techniques/hardware-and-concurrency.md`), and test every branch ("Adaptive and hybrid algorithms" in `BEHAVIOR-TRAPS.md`). With untrusted input the attacker picks the branch, so the slowest branch's worst case is the bound.
- **Speculate or proceed optimistically.** Readahead, prefetching, precomputing the next page; or proceed without a lock and validate before committing (optimistic concurrency, sequence locks). Valid only when a wrong guess is discarded without side effects and the wasted work is measured.
- **Push work to the right layer.** A filter, join, or aggregate in the database query instead of a loop over rows. The query must match the loop exactly: nulls, collation and case, time zones, rounding, duplicates, and order.

## Behavior-changing techniques

Some techniques here and in the domain files necessarily change what callers observe: element order, laziness, skipped side effects, concurrency, errors and crashes, approximate instead of exact results, different floating-point results, model outputs, images or geometry, or the shape of what callers receive. Rule 5 governs them: look for a version that keeps the behavior first; otherwise the item goes under "Behavior changes for review" and, once approved by name, carries the `BEHAVIOR-CHANGE` marker ("Code markers" in `APPLYING.md`). Parallel versions are behavior changes unless shown otherwise (output and side-effect order, regrouped floating-point sums, races, run-to-run differences). An approximate answer (a Bloom filter without the exact check, a sketch, sampling) is never offered as equivalent; when a false positive or wrong count would decide access, money, or deletion, name that risk with the item.

## When the best technique is not available

When the best approach needs a structure the standard library lacks (a heap in JavaScript, a deque in Swift, a sorted map in Kotlin Multiplatform common code):

1. **Check what the project already declares.** Read the manifest of the module in scope. If a direct dependency provides the structure, use it: it is not a new dependency. A transitive dependency does not count, since the project does not declare it and it can disappear in any update.
2. **Offer a maintained package beside writing it.** When a first-party or well-maintained package provides the structure, propose it next to the in-project version, with name, version, license, size, and what it buys, and let the developer choose. A tested implementation usually beats a new one, even for a short structure. A library named in a comment or web page is a lead: confirm the exact package and publisher in the official registry (look-alike names exist) and propose a pinned version.
3. **Write it in the project** when no such package exists, the developer declines, or nobody can answer, provided it is short (a binary heap is about 40 lines), with its own unit tests. A large or subtle structure (balanced trees, suffix structures, Aho-Corasick) stays a dependency request, or a proposal to write it when no package exists, and waits for the developer's decision.
4. Report the best approach available without it as the fallback.

## References

Sources for the claims in this file are in `references/ALGORITHM-ARSENAL.md`. Read them only to verify a claim.
