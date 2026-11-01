# Algorithm Arsenal

Use this file in Phase 3 (or write mode, step 4) to decide how to find candidate approaches: triage questions, routing by current complexity, lower bounds, and reformulation. The lookup tables of core techniques are in [CORE-TECHNIQUES.md](CORE-TECHNIQUES.md): load only the sections the routing below points to. Load [ADVANCED-TECHNIQUES.md](ADVANCED-TECHNIQUES.md) as well when the core techniques do not reach the lower bound, or when the problem falls in a specialized domain. It is a short index: it routes each domain (graphs and compiler analyses, optimization and scheduling, numerics, machine learning, images, geometry, games, storage and compression, concurrency, queues and latency, parsers, and others) to its own file under `techniques/`, and holds the rules shared by all of them.

Do not stop at the first technique that improves the bound. Check every section whose signals match, then check the combinations. When no row matches, or none reaches the lower bound, use [DISCOVERY.md](DISCOVERY.md) to derive an approach.

## Start with six questions

Before choosing any algorithm, ask:

1. **Is this work needed at all?** Before making work faster, check whether some of it can be avoided: output that is computed and then discarded inside the same function, a value recomputed when it is already available (from a parameter, a field, or an earlier step in the same call), or a query whose result the caller already has. Avoiding work is often the largest win, but it is also the easiest way to break something, so it is a proposal like any other, never a cleanup. Follow "Removing work" under rule 5 in `SKILL.md` and "Removed work" in `BEHAVIOR-TRAPS.md`:
   - **Prove the result is unused; never assume it.** Search every caller as in Phase 2 of `WORKFLOW.md` (reflection, dependency injection, serialization, configuration, templates, tests, scripts, other languages in the project). If the code is public or exported (a library API, a service endpoint, a plugin interface), callers outside the repository can exist and cannot be searched: treat its results as used.
   - **Prove the work has no other purpose.** It must not write, log, throw (including validation whose result is discarded), call collaborators, consume random numbers, acquire or release locks, change state that anything else reads, or exist for timing, ordering, or hardware reasons (constant-time code, delays, memory fences, volatile or device-register reads, cache or JIT warm-up).
   - **"Nothing has changed" is a caching claim.** Skipping a refresh, reload, or recomputation because the inputs seem unchanged needs proof of every input it depends on and a way to detect every change; treat it as a cache (`BEHAVIOR-TRAPS.md`, "Caching traps"), not as removal.
   - **Code that never runs is out of scope.** Unused functions, classes, and branches cost no execution time. Do not delete them as an optimization; at most mention them in the report.

   Report avoided work as "Work avoided," not as a complexity reduction, with the evidence for each check above.
2. **Am I repeating work?** Cache, memoize, hoist invariants, or precompute.
3. **Am I searching repeatedly?** Build an index, hash set, sorted structure, or lookup table.
4. **Am I keeping more information than I need?** Use rolling state, a bounded heap, a streaming algorithm, or a compact representation.
5. **Can I reorder or batch the work?** Sort offline, sweep, batch I/O, or process independent work together.
6. **What assumptions make the faster algorithm valid?** Monotonicity, static versus changing data, value bounds, sign of values, ordering requirements, purity, memory limits. Every technique row in `CORE-TECHNIQUES.md` and under `techniques/` has a "Valid when" column. Confirm each assumption from the code, not from intuition, and record the evidence in the report.

Most wrong optimizations come from a technique used outside its assumptions.

## Complexity reference

| Big O | Name | Growth | Common examples |
|---|---|---|---|
| O(1) | Constant | Excellent. Runtime does not depend on input size. | Array index access, stack push/pop, hash lookup (expected) |
| O(log n) | Logarithmic | Good. Grows by a constant step when input doubles. | Binary search, balanced-tree lookup, heap push/pop |
| O(n) | Linear | Fair. Grows in proportion to input. | Single loop, linear search, building a hash index |
| O(n log n) | Linearithmic | Fair to bad. Typical of efficient comparison sorting. | Merge sort, heapsort, average-case quicksort |
| O(n²) | Quadratic | Bad. Quadruples when input doubles. | Two nested loops, bubble sort, insertion sort |
| O(n^c), c > 2 | Polynomial | Poor. Worse with each level of nesting. | Triple nested loops, naive matrix multiplication |
| O(c^n), c > 1 | Exponential | Very inefficient. Doubles (or worse) with each added element. | Naive recursive Fibonacci, brute-force subsets |
| O(n!) | Factorial | Worst. Impractical beyond tiny inputs. | Brute-force permutations, naive traveling salesperson |

"Expected" means averaged over the algorithm's randomness or hash behavior; "amortized" means averaged over a sequence of operations; neither is a worst-case guarantee (rule 9).

## Analyzing recursive code

Recursive code is where complexity is most often misjudged. Write the recurrence from the code, then solve it:

- **Divide and conquer, T(n) = a·T(n/b) + f(n):** compare f(n) with n^(log_b a). If f grows polynomially slower, T(n) = Θ(n^(log_b a)). If they match up to a factor of log^k n, T(n) = Θ(n^(log_b a) · log^(k+1) n). If f grows polynomially faster (and a·f(n/b) ≤ c·f(n) for some c < 1), T(n) = Θ(f(n)). This is the master theorem. Example: T(n) = 2T(n/2) + n log n is Θ(n log² n), not Θ(n log n).
- **Uneven splits,** such as T(n) = T(n/3) + T(2n/3) + n: use the Akra-Bazzi method, or sum the recursion tree level by level. This one is Θ(n log n).
- **Shrinking by a constant:** T(n) = T(n − 1) + O(1) is O(n); T(n) = T(n − 1) + O(n) is O(n²); T(n) = 2T(n − 1) + O(1) is O(2ⁿ); T(n) = T(n − 1) + T(n − 2) + O(1) is Θ(φⁿ), about 1.618ⁿ.
- **Memoized recursion** costs the number of distinct subproblems times the work per subproblem, whatever the recurrence looks like.
- **Average case** needs a stated input distribution (rule 9). Quicksort with a fixed pivot rule makes about 1.39 n log₂ n comparisons on average over random orders, and n²/2 on its worst inputs, which may be the common ones (already sorted data).

When unsure, sum the recursion tree, then confirm the result with a doubling experiment (`BENCHMARKING.md`).

## Start from the current complexity

Find the row for the candidate's current cost, measured along the call chain (see Phase 2 in `WORKFLOW.md`), not only inside the function body. Start with the sections it names (quoted section names are in `CORE-TECHNIQUES.md` unless a file is named), then still check every other section whose signals match.

| Current cost | Usual cause | Look first at |
|---|---|---|
| O(n!) | Trying every ordering or assignment | Polynomial scheduling and assignment cases in `techniques/optimization-and-scheduling.md`; bitmask DP ("Bit manipulation"); sorting by a key when an exchange argument shows the order is determined ("Reusing work", greedy) |
| O(cⁿ) | Recursion that branches over overlapping subproblems; trying every subset | Memoization, DP, knapsack DP ("Reusing work"); meet-in-the-middle, branch and bound, constraint propagation ("Combinatorial search" in `techniques/sequences-dp-search.md`). If the problem is NP-hard in general, check whether small integer weights or targets allow a pseudo-polynomial DP, or whether the input size keeps exact search affordable |
| O(n³) or higher polynomial | Triple-nested loops; a quadratic loop that calls a linear helper | Precompute what the innermost loop recomputes (prefix sums, a hash index); sort plus two pointers ("Combinations"); "Dynamic programming optimizations" in `techniques/sequences-dp-search.md` |
| O(n²) | Nested loops over related collections; a linear search or front removal inside a loop | "Lookup, membership, counting", "Order and search", "Structures for repeated queries", "Combinations" |
| A product of size variables (O(n·m), O(V·E)) | For each A, scan all B | "Invert the loop" under "Reformulate before choosing": index one side once. Name every variable; the right fix depends on which one is large |
| O(n log n) | A sort, or n heap or tree operations | Whether the order is observable at all; top-k, min, or max without a full sort ("Priority and selection"); non-comparison sorts for bounded keys |
| O(n) per call, called many times | Recomputing from scratch on every call | "Precompute once, query many times" and "Incremental maintenance" under "Reformulate before choosing"; "Structures for repeated queries"; "Changing graphs" in `techniques/graphs-and-trees.md` when a graph result is rebuilt after each change |
| O(n²) over objects in space | Checking every pair of objects for distance, overlap, or collision; every ray against every object | "Spatial data" in `techniques/spatial-data.md`, "Computational geometry and CAD" in `techniques/geometry-and-cad.md`, and "Games and real-time simulation" in `techniques/games-and-simulation.md` |
| O(N·k²) over pixels or samples | A filter that visits every neighbor of every pixel or sample | "Image, video, and signal processing" in `techniques/images-and-signals.md` |
| Model training or inference slower than expected | Recomputed attention, host and device synchronization, data loading, or element-by-element loops over tensors | "Machine learning and AI" in `techniques/machine-learning.md` |
| Latency high while each step's own work is small (time spent waiting in queues, pools, locks, or for remote replies), or tail latency far above the median | Utilization near capacity, head-of-line blocking, fan-out, or unbounded queues, not the algorithm | `techniques/queues-and-latency.md` |
| Cost dominated by page or disk I/O, cache misses, branch misses, or cache hit rate rather than operation count | Data layout, storage structure, or eviction policy, not the algorithm | "Storage and indexing" in `techniques/data-at-scale.md`, "Memory locality" in `techniques/hardware-and-concurrency.md`, and "Caching and eviction" in `techniques/data-structures.md` |

## Required enumeration

For each candidate, write down:

1. The abstract problem statement.
2. The lower bound and its reason.
3. Every matching signal from the tables in `CORE-TECHNIQUES.md` and the domain files routed by `ADVANCED-TECHNIQUES.md`.
4. Candidate approaches in proportion to difficulty (rule 6). If the strongest candidate reaches the lower bound, needs no new dependency (the standard library, or a structure the project already has), and has no behavior risks, name it and briefly explain why alternatives are unnecessary. Otherwise, at least three plausible approaches, including at least one combination when the problem has more than one dimension. Never invent alternatives to meet a quota.
5. For each approach: the assumptions it needs and the evidence from the code that they hold.
6. Whether the approach changes any observable behavior (see "Behavior-changing techniques" below).
7. The chosen approach, and why the others lost.

## Lower bounds

A lower bound tells you when to stop. Common ones:

- **Must read the input:** if the answer can depend on every element, Ω(n). No sublinear algorithm exists without preprocessing or extra structure (sortedness, an index).
- **Comparison sorting:** Ω(n log n). Beat it only with non-comparison sorts (counting, radix, bucket) when keys are bounded integers or fixed-width.
- **Search in unsorted data:** Ω(n) per query. Repeated queries change the picture: build an index once in O(n), then answer each in O(1) expected.
- **Search in sorted data:** comparison-based lookup takes Θ(log n). For repeated exact-key queries, a hash index gives O(1) expected lookup after O(n) expected preprocessing and O(n) extra space. It does not pay off for a one-off query, it must preserve the original equality semantics, and its worst-case lookup is slower.
- **Output size:** if the result has k elements, Ω(k). Listing all pairs is Ω(n²) when there can be n² pairs.
- **No known faster algorithm:** some problems have only conjectured bounds. No algorithm substantially faster than O(n²) is known for 3SUM (three elements summing to a target) and the many problems that reduce to it. No polynomial algorithm is known for NP-hard problems such as 0/1 knapsack, subset sum, or the traveling salesperson. Stop there and say the bound is conjectured; do not promise better.
- **Repeated calls:** when a function is called m times on the same or slowly changing data, the real cost is total work across all calls. Preprocessing once plus cheap queries can beat any per-call algorithm.
- **No bound can be established:** many real costs have no known lower bound, or none you can derive from the code: work dominated by a database query plan, network round trips, lock contention, cache behavior, hardware, or the distribution of the data. Do not invent one. Report the basis as "unknown," state why, and give the strongest bound you can support instead ("at least one pass over the input," "at least one round trip per distinct key," "at least the size of the output"). Then keep evaluating candidates as rule 6 requires: an unknown bound means you cannot prove you are done, so record which approaches you considered and why you chose the one you did.

If the chosen approach is above the lower bound, say why: the better bound needs an unapproved dependency, needs preprocessing that the call pattern cannot amortize, needs an assumption the code does not satisfy, or has constant factors that lose at realistic sizes (backed by a benchmark).

## Reformulate before choosing

Many large wins come from changing the problem rather than speeding up the loop. These are the common patterns; `DISCOVERY.md` has the full method for deriving new ones:

- **Precompute once, query many times.** Move invariant work out of loops and out of repeated calls: build a map, prefix array, or sorted copy once.
- **Invert the loop.** Instead of "for each A, scan all B," index B once and look up each A.
- **Count the complement.** Counting what fails can be cheaper than counting what passes.
- **Transform the key space.** Coordinate compression, normalizing keys, sorting by one dimension to make another dimension a sweep.
- **Offline processing.** If all queries are known up front, sort or batch them.
- **Incremental maintenance.** Update a running result when data changes instead of recomputing from scratch.
- **Process changes, not snapshots.** When the source can report what changed (a write-ahead or replication log, change data capture, file-system notifications, an event stream), consume the changes instead of rescanning the whole dataset to find them. The cost per update becomes proportional to the change, not the data. See "Change propagation" in `techniques/data-at-scale.md`.
- **Cheap check first.** Run an inexpensive test that can only rule candidates out (a Bloom filter, min and max per block, a bounding box, a length or hash comparison) before the expensive exact check. It may pass candidates that later fail, but it must never reject one the exact check would accept.
- **Choose by the input.** When different implementations win on different inputs, pick one per call from measured properties of the input: size below a crossover, presorted runs, many duplicates, density, key width, or CPU features. Query planners choosing a join algorithm, pattern-defeating quicksort, Timsort, size-class allocators, and `memcpy` selected by size and instruction set all work this way. Count the cost of classifying the input, measure crossovers as in the crossover row of `techniques/hardware-and-concurrency.md`, and test every branch (see "Adaptive and hybrid algorithms" in `BEHAVIOR-TRAPS.md`).
- **Speculate or proceed optimistically.** Do likely work before it is requested (readahead, prefetching, precomputing the next page), or proceed without a lock and validate before committing (optimistic concurrency, sequence locks). Valid only when a wrong guess is discarded without side effects and the retry or wasted work is measured. See `techniques/hardware-and-concurrency.md` and `techniques/data-at-scale.md`.
- **Push work to the right layer.** A filter, join, or aggregate in the database query instead of in a loop over rows.

## Behavior-changing techniques

Some techniques in `CORE-TECHNIQUES.md` and the domain files necessarily change observable behavior: element order, laziness, side effects skipped, concurrency, error and crash behavior, approximate instead of exact results, different floating-point results, different model outputs, different images or geometry, or the shape of what callers receive. Rule 5 applies to every one of them:

- Never apply a behavior-changing optimization silently.
- Document it in the report under "Behavior changes for review," with the exact behavior before and after.
- Apply it only after the developer explicitly approves that item (a general "apply all" is not approval), then add the `BEHAVIOR-CHANGE` marker from `REPORTING.md`.

This includes changes that look like improvements: a function that fails faster, returns results in a "more sensible" order, or no longer throws an exception callers may rely on. Those are behavior changes, and the developer decides.

The one exception is a bug removed as a side effect of the best optimization, such as an iterative rewrite that no longer overflows the stack. Rule 4 in `SKILL.md` governs it.

## When the best technique is not available

If the best approach needs a structure the standard library lacks (for example, a heap in JavaScript, a deque in Swift, a sorted map in Kotlin Multiplatform common code):

1. Prefer a small, well-tested implementation inside the project when it is short (a binary heap is about 40 lines). Give it its own unit tests.
2. If a robust implementation is large or subtle (balanced trees, suffix structures, Aho-Corasick), propose the dependency to the developer with its name, version, license, size, and what it buys, and wait for permission.
3. Report the best approach available without the dependency as the fallback.

## References (for verifying claims; not required reading)

- Cormen, Leiserson, Rivest, and Stein, *Introduction to Algorithms*, 4th ed. (2022), chapter 4 (recurrences and the master theorem).
- Mohamad Akra and Louay Bazzi, "On the Solution of Linear Recurrence Equations," *Computational Optimization and Applications* 10(2), 1998.
- Robert Sedgewick and Philippe Flajolet, *An Introduction to the Analysis of Algorithms*, 2nd ed. (2013): average-case analysis, generating functions.
- Donald E. Knuth, *The Art of Computer Programming*, Vol. 1, section 1.2 (mathematical preliminaries).
