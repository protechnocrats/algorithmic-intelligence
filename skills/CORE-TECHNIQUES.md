# Core Techniques

Lookup tables for known techniques: the signal in code, the technique, the conditions under which it is valid, and the typical result. `ALGORITHM-ARSENAL.md` routes to the sections; domain-specific techniques are under `techniques/`, indexed by `ADVANCED-TECHNIQUES.md`.

**Contents:** Signals and techniques · Production patterns · Bit manipulation · Combinations

## Signals and techniques

How to read the tables here and in the domain files:

- "Typical result" is the change in asymptotic cost when every "Valid when" condition holds. Bounds are worst case unless marked expected, amortized, or average; "in practice" marks workload-dependent speedups, not complexity improvements.
- Build cost and memory are stated separately from per-query cost; count both against the real call pattern. A query returning k results costs at least O(k) more.
- A "Valid when" condition holds only if the code enforces it or builds the data that way, for every input it accepts. A comment or name that claims it does not count.
- Expected bounds assume nobody picks bad inputs. With untrusted input, hashing, randomized pivots, rolling hashes, and backtracking are judged by their worst case (`techniques/hostile-inputs.md`).

### Lookup, membership, counting

| Signal in code | Technique | Valid when | Typical result |
|---|---|---|---|
| `contains`, `indexOf`, `find`, `includes` inside a loop | Hash set or hash map built once | Equality and hashing match the original comparison exactly (NaN and signed zero differ between `==`, `equals`, `indexOf`, and hash structures: in JavaScript `indexOf(NaN)` is −1 while `includes` and `Set.has` find it); `indexOf` also returns a position, which a set cannot give | O(n·m) → O(n + m) expected |
| A set or index built inside the predicate or loop body (`filter { it in other.toSet() }`) | Build it once, outside | The source does not change during the loop; equality matches as in the row above | O(n·m) → O(n + m) expected; it looks already fixed because a set appears in the code |
| Counting occurrences with nested loops | Hash map of counts; counting array | Counting array: small, dense integer keys with the range enforced in code (a range taken from the input's maximum can allocate unbounded memory) | O(n²) → O(n) expected (array: worst case) |
| Grouping by a key with repeated filters | Single-pass grouping into a map | Group order and item order match the original | O(n·g) → O(n) expected |
| Keys are small dense integers | Plain array indexed by key | Key range known, small enough to allocate, and enforced in code | Same Big-O as hashing, but O(1) worst case with smaller constants |
| Duplicate detection | Hash set; or sort then compare neighbors | Sorting: the input may be copied or reordered and an ordering exists | O(n²) → O(n) expected, or O(n log n) |
| Repeated range sums | Prefix sums | Data does not change between queries (otherwise a Fenwick tree or rebuild); sums cannot overflow differently; in floating point, a difference of prefix sums rounds differently from a direct sum and loses precision to cancellation (behavior change) | O(n) per query → O(1) after O(n) setup |
| Many range increments, read at the end | Difference array, then one prefix-sum pass | All updates happen before reads | O(n·q) → O(n + q) |
| Repeated range XOR | Prefix XOR | Data does not change between queries | O(n) per query → O(1) after O(n) setup |
| Many range minimum/maximum queries | Sparse table | Data does not change; the operation is idempotent (min, max, gcd, and, or) | O(n) per query → O(1) after O(n log n) setup and memory |
| Union, intersection, difference of integer sets | Bitset, or merge of sorted lists | Bitset: small integer universe. Merge: both inputs sorted | O(n·m) → O(u/w) word operations or O(n + m) |

### Order and search

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Linear scan of sorted data | Binary search | Sorted by the search's comparator, which is consistent (NaN, mixed types, or locale-dependent comparison break it); random access; the match returned among duplicates and the not-found result match the original | O(n) → O(log n) |
| Searching a sorted array with near-uniformly distributed keys (sequential IDs, steady-rate timestamps) | Interpolation search | Keys measured as near uniform; skewed or adversarial keys make it O(n), so fall back to binary search after a few probes | O(log n) → O(log log n) expected on uniform keys |
| Sorted data where the target is usually near the start or the length is unknown (streams, merge loops) | Exponential (galloping) search | Same comparator; same match among duplicates | O(log n) → O(log i) for a target at position i |
| First index or smallest value that satisfies a condition | Binary search on a monotonic predicate | Predicate monotonic over the range; boundary behavior (empty range, no match, all match, duplicates) matches the original | O(range · check) → O(log range · check) |
| Pair or triple search over sorted data | Two pointers | Sorted; moving a pointer provably excludes the skipped candidates | O(n²) → O(n) after sorting |
| Aggregate over every fixed-size window | Running aggregate updated as the window slides | The aggregate is invertible (sum, count, XOR); in floating point, add-and-subtract rounds differently from summing each window (behavior change) | O(n·k) → O(n) |
| Minimum or maximum of every fixed-size window | Monotonic deque | When the position of the extreme is returned, the tie rule (strict or non-strict pop) matches the original | O(n·k) → O(n) amortized total |
| Longest or shortest contiguous run meeting a condition | Variable sliding window | The condition is monotonic as the window grows or shrinks (sums of non-negative values, "at most k distinct"). Negative values break it whenever the code accepts them, whatever the data usually holds | O(n²) → O(n) |
| Subarrays with an exact target sum, values of any sign | Prefix sum + hash map of prefix counts | Exact-equality condition | O(n²) → O(n) expected |
| Sum constraints with negative values (shortest subarray with sum ≥ k, and similar) | Prefix sums + monotonic deque, or prefix sums + sorted structure | Depends on the exact condition; prove the deque invariant | O(n²) → O(n) or O(n log n) |
| Next greater or smaller element, spans, histogram areas | Monotonic stack | Strict or non-strict comparison matches the original for equal elements | O(n²) → O(n) amortized total |
| Overlapping intervals, merging ranges | Sort by start, then sweep | Endpoint semantics match (closed or half-open, whether touching intervals merge); output order matches | O(n²) → O(n log n) |
| Events over time (concurrent sessions, resource counts) | Sweep line over sorted endpoints | Tie order of start and end events matches the original | O(n²) → O(n log n) |
| Sorting input that is often partly sorted or has many equal keys | Adaptive sorting: natural merge sort or Timsort (stable), pattern-defeating quicksort (unstable), three-way partitioning for duplicates | Stability matches: replacing a stable sort with pdqsort or introsort reorders equal elements (behavior change). A comparator that is not a consistent total order (NaN, mixed types) gives a different order, or an exception in some Timsort implementations. Measure how sorted real inputs are | O(n log n) → O(n) on presorted input; O(n log d) expected with d distinct keys (three-way quicksort with random pivots) |
| A sort key or comparator that does expensive work (parsing, formatting, a lookup) | Decorate, sort, undecorate: compute each key once, sort the pairs by key, drop the keys; or the language's caching sort (the language file says which APIs cache, and several key-named ones do not) | The key is pure and its cost matters (a field read does not). The same sort keeps the same tie behavior. The key now runs on every element, including inputs the original never called it on ("Key functions" in `BEHAVIOR-TRAPS.md`) | O(m·n log n) → O(m·n + n log n) for key cost m |
| `indexOf` or a linear search used as a sort key (a custom display order) | Map from value to rank, built once | Values missing from the order rank as the original did (`indexOf` gives −1, so they sort first); a value listed twice keeps its first index | O(n·m log n) → O(m + n log n) expected |
| A full sort to take one extreme (`sorted().first()`) | Single-pass minimum or maximum | The same one of several equal elements comes back ("Ties" in `BEHAVIOR-TRAPS.md`), and empty input behaves the same | O(n log n) → O(n) |
| Sorting by a boolean or a few enum values | One stable pass into a bucket per value, then concatenate in comparator order | The original was stable, or the order of ties is unobservable | O(n log n) → O(n + k) for k values |
| A sort over data that is already sorted | Drop the sort, with a test pinning the upstream order ("Pin what the change assumes" in `DIFFERENTIAL-TESTING.md`) | Every path into it is sorted by exactly this comparator, tie order included, and nothing between reorders it (filters and maps keep order; merges and concatenations do not). A database `ORDER BY` often differs on collation and ties. It is removed work (rule 5) | Removes the sort. An adaptive sort already takes about O(n) comparisons on sorted input, so predict a constant-factor gain unless the comparator is expensive |
| Re-sorting after every append | Sort once before the first read when reads are rare; otherwise binary insertion after equal elements, or a sorted structure | Nothing reads between appends in the deferred version; insertion keeps a stable sort's tie order | O(m·n log n) for m appends → O(n log n) when deferred |
| Concatenating two sorted lists, then sorting | Linear merge, taking from the first list on ties | Both lists sorted by the same comparator; matches a stable sort of the concatenation | O(n log n) → O(n); a constant factor when the sort is adaptive |
| Sorting bounded integers | Counting sort or radix sort | Counting sort: key range k small relative to n and enforced in code (a 32-bit range makes the count array far larger than the input; negative keys need an offset). Radix sort: fixed-width keys. Stable variant when equal keys carry other data | O(n log n) → O(n + k) for counting sort; O(d·(n + b)) for radix sort with d digits in base b |
| Removing from or adding at the front of an array; removing from the middle when order does not matter | Deque or ring buffer for the ends; swap-with-last removal for the middle | Swap-with-last changes element order, so only when no caller observes order. Neither helps middle insertion, which needs a linked list with node handles, a gap buffer when edits cluster, or a balanced tree | O(n) per operation → O(1) (deque: amortized at the ends) |
| Longest increasing or non-decreasing subsequence | Patience sorting + binary search | Strict or non-strict comparison matches; when the subsequence itself is returned, which of several longest ones is chosen matches (predecessor links pick a different one than the O(n²) DP) | O(n²) → O(n log n) |

### Priority and selection

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Sorting everything to take the top k | Heap of size k; or quickselect, then sort only the k selected | Tie handling matches; k ≤ n and k = 0 handled as the original did. Quickselect reorders its input: work on a copy | O(n log n) → O(n log k), or O(n + k log k) expected |
| Top k for small k, where ties have to keep input order | Stable bounded insertion: keep a sorted buffer of at most k; for each element, skip it if the buffer is full and it is not ahead of the last entry; otherwise binary-search the position after equal elements, insert, and drop the last entry if over k | k small enough that shifting is cheap: compare with a heap on sequence numbers at realistic k, and use the heap for large k or untrusted input, whose order can force a shift per element. The result equals the first k of a stable sort; test it against that. For descending order use a descending comparator, never a reversed result, which reverses ties | O(n log n) → O(n log k) comparisons, with O(n·k) element moves in the worst case |
| k-th smallest or median, one-off | Quickselect; median-of-medians for a worst-case guarantee | Input may be copied or reordered. A fixed pivot rule is O(n²) on inputs an attacker can build: random pivots from an unpredictable source, or a worst-case method, for untrusted input | O(n log n) → O(n) expected, or O(n) worst case |
| Repeatedly taking the minimum of a changing set | Binary heap | Build with heapify. A scan returns the first minimum, a heap an arbitrary one (and `heapq` compares the next tuple field or raises): the choice among equal keys is unobservable, or each entry carries a sequence number | O(n) per extraction → O(log n); heapify O(n) |
| Running median | Two heaps | Median of an even count defined as in the original (lower, upper, or average); duplicates kept | O(n) per insert → O(log n) |
| Minimum and maximum of a changing set | Sorted multiset, or sorted map of value → count (a plain sorted map merges equal values, so one removal drops every copy) | Two heaps also work but need lazy deletion | O(n) per query → O(log n) |
| k-th element of a changing ordered collection | Order-statistic tree, or a Fenwick tree over compressed values | Fenwick: all values known up front | O(n) → O(log n) |
| Merging k sorted lists | Heap of list heads | Every list sorted by the merge's comparator; ties broken by list index if the order among equal elements is observable | O(N·k) → O(N log k) |

### Structures for repeated queries

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| "Are these connected / in the same group?" with merges | Union-find with path compression and union by rank or size | Merges only (no splits) | O(α(n)) amortized per operation (α ≤ 4 for any practical n) |
| Prefix matching, autocomplete, word lookup | Trie | Word set built once or changes rarely; case and normalization semantics preserved; memory counted per node, and bounded when untrusted parties supply the words | Build O(L) for L total characters; lookup O(m) for a length-m query, plus O(k) for k matches |
| Range sums or counts with point updates | Fenwick (binary indexed) tree | The operation is invertible (sum, count, XOR) | Query O(n) → O(log n); point update O(1) → O(log n) |
| Range queries with point updates, any associative operation (min, max, gcd) | Segment tree | The operation is associative | Query O(n) → O(log n); point update O(1) → O(log n) |
| Range updates and range queries together | Segment tree with lazy propagation | Updates compose with each other and with the aggregate | O(n) per operation → O(log n) |
| Floor, ceiling, predecessor, successor, ordered iteration with inserts | Balanced BST / sorted map | The comparator is a consistent total order, consistent with equality | O(n) → O(log n) |
| Fixed set of keys known in advance | Precomputed lookup table, or perfect hashing | Key set never changes at runtime | O(1) worst case |
| LRU or bounded cache | The language's bounded LRU where it has one; otherwise an insertion-ordered hash map, re-inserting on each hit; a hash map + doubly linked list only when neither exists (see language files) | The cached function is pure; the key holds every input the result depends on, including user, tenant, and permission context; invalidation stated (cached permissions or sessions drop on revocation) | O(1) expected per operation, bounded memory |

### Graphs

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Shortest path, unweighted | BFS | Every edge costs the same; if observable, the path returned among equals matches | Path enumeration → O(V + E) |
| Shortest path from many sources at once | Multi-source BFS | Unweighted; each node needs only its distance to the nearest source (and which source). Per-source distances still need k runs | k BFS runs → one O(V + E) |
| Shortest path, weighted | Dijkstra with a heap | Non-negative weights (negative weights: "Graphs" in `techniques/graphs-and-trees.md`). When E is near V², the O(V²) array version beats the heap | O((V + E) log V) with a binary heap on sparse graphs, O(V²) with an array on dense graphs |
| Shortest path, weights 0 or 1 | 0-1 BFS with a deque | Weights exactly 0 or 1 | O((V + E) log V) → O(V + E) |
| Dependency order, build order | Topological sort (Kahn or DFS) | DAG; cycles detected and reported as the original did; order among independent nodes matches where observable (Kahn with a FIFO, a stack, or a sorted frontier, and DFS, each give a different valid order) | O(V + E) |
| Directed cycle or deadlock detection | Three-color DFS, or topological-sort failure | Which cycle is reported, and the error raised, match when callers read them | O(V + E) |
| Connected regions in a grid | Flood fill with iterative BFS or DFS | Recursion depth ("Errors and limits" in `BEHAVIOR-TRAPS.md`) | O(V + E) |
| Repeated reachability or recomputation over a static graph | Precompute components, memoize per node | Graph does not change between queries. Components answer reachability only in undirected graphs; for directed graphs, condense strongly connected components and precompute reachability over the DAG (O(V·(V + E)) time, O(V²) bits) only when the query count justifies it | Per-query traversal → O(1) per query |
| Minimum spanning tree | Kruskal (sort + union-find) or Prim (heap) | Tie-breaking among equal-weight edges matches when the chosen tree is observable | O(E log E) |

### Reusing work

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Recursion that recomputes the same arguments | Memoization | The function is pure ("Hidden inputs" in `BEHAVIOR-TRAPS.md`); the key includes every argument it reads; subproblems actually repeat (if rare, a cache only costs memory); bounded; scope and invalidation stated | Exponential → O(distinct states × work per state) |
| Optimal-choice problems over sequences, grids, subsets | Dynamic programming | Optimal substructure and overlapping subproblems | Exponential → O(states × transitions per state) |
| DP where each state depends only on the previous row or a few previous states | Rolling arrays / state compression | Only the final value is needed: reconstructing the chosen solution needs the full table or Hirschberg-style recomputation | Memory only: O(n·m) → O(m). Time unchanged |
| Deep recursion over overlapping subproblems | Bottom-up DP | Recursion depth ("Errors and limits" in `BEHAVIOR-TRAPS.md`) | Same time when most states are reachable; when few are, bottom-up fills states the memoized version never visits, so measure. No call-stack depth |
| Locally optimal choice is provably globally optimal | Greedy, with an exchange argument written down | The proof holds for every input the code accepts | Polynomial → O(n log n) or O(n) |
| Subset or capacity problems with small integer targets | Knapsack DP indexed by achievable sum | Integer weights; target T bounded in code, not taken from input (a request-supplied T allocates an n·T table) | O(2^n) → O(n·T) (pseudo-polynomial) |
| Counting the number of ways, not enumerating them | DP with counting | A numeric type or modulus that cannot overflow differently from the original | Enumeration → O(states × transitions per state) |
| Enumerating solutions with many dead ends | Backtracking with pruning, constraint propagation, branch and bound ("Combinatorial search" in `techniques/sequences-dp-search.md`) | Pruning never discards a valid solution; result order matches if observable; with untrusted input the exponential worst case is reachable, so keep the original's input size or work limit | Large practical speedups; worst case stays exponential |
| A sum, maximum, or count recomputed over a collection after each append | Keep a running value | Every path that changes the collection updates it; a removal can force a recompute for maximum or minimum; in floating point a running sum can round differently (behavior change) | O(n²) → O(n) |
| Tree height, size, or depth recomputed at each node | One bottom-up pass that returns the value upward | Recursion depth ("Errors and limits" in `BEHAVIOR-TRAPS.md`); the order nodes are visited is unobservable or kept | O(n²) on skewed trees → O(n) |
| Loops that compute sums of series, counts, arithmetic progressions | Closed-form formula | Cannot overflow or round differently from the loop | O(n) → O(1) |
| Repeated exponentiation, linear recurrences | Binary exponentiation; matrix exponentiation | The operation is associative; with big integers each multiplication grows costlier, so count bit operations | O(n) → O(log n) multiplications; for an order-k recurrence, O(k·n) → O(k³ log n), which loses when k is large and n small |
| Work that splits into independent halves | Divide and conquer | Halves independent; combining costs less than the work saved; recursion depth bounded | O(n²) → O(n log n) in many cases |

### Strings

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| String concatenation in a loop | Builder or join | Measure the starting cost: CPython's in-place `+=` and JavaScript ropes are already near-linear, Java's `+` is not. Null and non-string operands convert as before (Java `+`, `StringBuilder`, and `String.join` all write `"null"` for a null element; other joiners, such as Guava's `Joiner` or `Collectors.joining` over a mapping that dereferences the element, throw instead) | O(n²) → O(n) |
| Substring search with long patterns or many searches | KMP, Z-algorithm, or the platform's optimized search | Same matching semantics (case, culture, overlapping matches) | O(n·m) → O(n + m) |
| Comparing many substrings | Rolling hash with prefix hashes and powers | Every hash match confirmed by direct comparison. With untrusted input, a random base per run and a large prime modulus (2^61 − 1, or two moduli): a fixed base lets an attacker force collisions, and modulus 2^64 by overflow collides on Thue-Morse strings for any base. Text with many true matches ("aaaa…") returns to O(n·m): use KMP or the Z-algorithm there | O(n·m) → O(n + m + z·m) expected for z true matches; O(1) per substring hash after O(n) setup |
| Anagram or character-frequency checks | Fixed-size count array | Small, known alphabet; characters outside it (non-ASCII, combining marks, case variants) behave as in the original | O(n log n) → O(n) |
| Many patterns against one text | Aho-Corasick | Same overlapping-match, case, and normalization semantics, and the same match reported first when patterns share positions | O(n·p) → O(n + L + z), L total pattern length, z matches |
| Many repeated string comparisons or groupings | Canonical keys, interned IDs, or sorted signatures | Canonicalization preserves the original equality exactly (case folding and Unicode normalization vary by locale and form: Turkish dotted i, composed and decomposed accents); interning untrusted strings needs a bound | O(length) comparisons → O(1) ID comparisons |

## Production patterns

In real systems, removing repeated work, allocation, and I/O often matters more than changing the algorithm. Most of these change behavior subtly; the last column says what to check.

| Signal | Technique | Valid when | Behavior risk |
|---|---|---|---|
| Same expensive expression computed in every loop iteration | Hoist it out of the loop | No side effects; its inputs do not change in the loop | Low |
| A property or getter that copies, sorts, or builds its result, read in a loop | Read it once into a local | The value does not change during the loop, or a single snapshot is what the loop needs; the getter has no effects | The loop no longer sees changes made while it runs ("Moved reads" in `BEHAVIOR-TRAPS.md`) |
| Recursion that copies a slice on each call | Pass indices or a view | The underlying data is not changed during the recursion; index bases match | Aliasing; views can keep the whole base alive |
| Log message or its arguments built when that level is off | The logging library's lazy or parameterized form, or a level check | Argument expressions have no effects; output at enabled levels is identical | "Logs, metrics, and audit records" in `BEHAVIOR-TRAPS.md` |
| Exceptions used for normal control flow in a hot loop (parse, catch, continue) | A non-throwing variant, or a check first | Exactly the same inputs are accepted; what the catch block did still happens. Measure, since the cost depends on the runtime | "Non-throwing variants" in `BEHAVIOR-TRAPS.md` |
| Repeated parsing, regex compilation, formatter creation | Create once and reuse | The reused object is safe to share across threads; a pattern built from input stays escaped as before (backtracking regexes: `techniques/hostile-inputs.md`) | Shared state |
| Objects allocated in a hot loop | Reuse buffers or objects; primitive representations | No caller, closure, or other thread retains the reused object | Aliasing and thread safety |
| Whole collection copied on every update to stay immutable (spread in a reducer, copy-on-write state) | Build once and freeze, or a persistent structure with structural sharing (`techniques/specialized-structures.md`) | No caller mutates or compares versions in a way the new structure changes | Reference equality and iteration order |
| Large collection copied only to read or iterate | View, iterator, span, or reference | The source is not mutated while the view is alive | Aliasing |
| Only the first match or a yes/no answer is needed | Early exit, short-circuit evaluation, lazy iteration | Skipped iterations have no side effects. Comparisons of secrets (tokens, MACs, password hashes) stay constant-time: an early exit leaks the position of the first mismatch through timing | Behavior change if skipped iterations had effects or could throw |
| Many tiny objects or linked structures | Contiguous arrays, flat maps, packed representations | Callers do not rely on object identity | Identity |
| Expensive result that depends on a small set of inputs | Memoization or caching with explicit bounds, scope, and invalidation | Pure, including hidden inputs (time, locale, configuration, user or tenant context) | Staleness if not pure; data leaking across users if the key omits user, tenant, or permission context |
| Database rows fetched one at a time (N+1) | Batch loading, joins, eager loading, DataLoader-style batching | The batched query returns the same rows (duplicates, missing keys, filters); batches stay under the database's parameter and query-size limits | Result order, transaction boundaries, partial failure |
| Whole dataset loaded when a subset is used | Projection, filtering at the source, streaming, pagination | Every caller uses only the subset | Behavior change if callers receive different objects or pages |
| Independent network or I/O operations run sequentially | Batching or bounded concurrency | Truly independent (no shared state, ordering, or rate limit between them); the concurrency limit is fixed, not taken from input | Ordering, error handling, rate limits |
| Unbounded queues or unbounded concurrent requests | Backpressure, bounded queues, admission control (`techniques/queues-and-latency.md`) | The rejection or blocking signal becomes part of the contract | Behavior change under load |
| Full recomputation after a small change | Incremental computation, dependency tracking | Every dependency is tracked | Staleness if a dependency is missed |
| Heavy work on a UI thread, event loop, or request thread | Move work elsewhere; precompute; cache derived values | Threading is part of the contract (rule 11) | Behavior change |

### Database queries

Base any index or query change on the actual plan (`EXPLAIN`, `EXPLAIN ANALYZE`, or the equivalent) on representative data, not on the SQL text. `EXPLAIN ANALYZE` executes the statement: run it only on a local or test database, and for a writing statement only inside a transaction you roll back. Production plans and anything against a shared database are the developer's to run.

| Signal | Technique | Valid when | Behavior risk |
|---|---|---|---|
| Full table scans for selective filters or joins | Index on the filtered or joined columns; composite index with equality columns first, then range or sort columns | The plan shows the scan and the filter is selective | Schema change: slower writes, more storage, locking during creation |
| Predicates that prevent index use (functions or casts on indexed columns, leading wildcards, implicit type conversions) | Rewrite the predicate so the index applies, or index the expression | The rewrite is exactly equivalent, including nulls, collation, and time zones | Subtle result changes if not exact |
| `ORDER BY` or `DISTINCT` the caller does not need | Remove it | Every caller checked | Behavior change if any caller depends on order or uniqueness |
| Deep `OFFSET` pagination | Keyset (seek) pagination on an indexed, unique ordering | A unique, stable ordering key (add a tiebreaker column if needed); clients can pass a cursor. The cursor is untrusted input: it carries only ordering key values, every filter and tenant or permission condition is reapplied from the authenticated request, and it is validated or signed | Page boundaries under concurrent writes, and the API shape |
| `SELECT *` or whole entities loaded for a few fields | Projection of only the needed columns | Every caller uses only those fields | Behavior change if callers receive a different type |
| A plan regresses or picks a poor join order although indexes exist | Refresh planner statistics (`ANALYZE` or equivalent), add extended statistics for correlated columns, re-check the plan; hints only as a last resort | Statistics change other queries' plans too: compare them before and after | Estimates match the data, so the planner can choose the plan the indexes allow |
| Counting rows only to check existence | `EXISTS` or `LIMIT 1` | The count is used for nothing else (not returned, logged, or compared with a number) | Low; behavior change if the count was used |

## Bit manipulation

Bits help when they reduce complexity or replace a heavier structure. Expressions use C-style operators; the language files give exact syntax (Kotlin uses `and`, `or`, `xor`, `shl`, `inv()`).

| Use | How | Valid when | When it helps |
|---|---|---|---|
| Small set of flags (permissions, features, states) | One `Int` or `Long` as a bitmask; `OptionSet` in Swift; `EnumSet` in Java; `[Flags]` enum in C# | Flag count fixed below the word width; iteration order over flags, if observable, matches | Set operations become single O(1) instructions; no allocation |
| Set of integers in a known small range | Bitset (`BitSet`, `BitArray`, or an array of words) | Range enforced in code, not taken from the input's maximum; negative values offset or rejected as the original did | Membership, union, intersection in O(u/64) word operations |
| Test, set, clear, toggle bit i | Mask `1 << i` with `&`, `\|`, `& ~`, `^` | 0 ≤ i < width, checked: shifting by the width or more wraps or is undefined (JavaScript masks the shift count to 5 bits) | O(1) state checks |
| Count set bits | Built-in popcount (see language files) | None beyond the type's width | One instruction instead of a loop |
| Lowest set bit | `x & -x`; trailing-zero count | Unsigned types, or a signed type in a language that wraps (Java, Kotlin, C#). In C and C++, negating the minimum signed value is undefined behavior, and so is `~x + 1`: convert to the unsigned type first. x = 0 handled as the original did | Iterate only set bits: O(set bits) instead of O(width) |
| Power of two check | `x > 0 && (x & (x - 1)) == 0` | Zero and negative values answer as the original did | O(1) |
| Find the unique element when all others appear twice | XOR of all elements | The code guarantees that shape: otherwise it returns a wrong value silently, where the original may have failed or returned "not found" | O(n) time, O(1) space |
| Enumerate all subsets of a small set | Iterate masks 0 until 2^n | n bounded in code below the word width (2^n overflows at 31 or 63 for signed types); enumeration order matches when observable | Simpler and faster than recursive generation |
| Enumerate all submasks of every mask | `for (s = m; s > 0; s = (s - 1) & m)`, which skips the empty submask | As above; the empty submask handled separately if the original included it | O(3^n) total instead of O(4^n) |
| Subset DP (assignments, small traveling salesperson) | DP indexed by bitmask | n bounded in code so 2^n · n fits memory; ties among equal-cost solutions resolved as the original did when the solution is returned | O(n!) → O(2^n · n²) time, O(2^n · n) memory |
| Packing several small fields into one key | Shifts and masks into a `Long` | Each field checked to fit: a negative or oversized value sign-extends or spills into the next field, and distinct keys collide | Composite keys without allocating pair objects |

Watch for signed versus unsigned shifts, integer width (JavaScript bitwise operators work on 32-bit signed integers), and shifts by the full width. More bit techniques: `techniques/math-and-numerics.md` (XOR basis, GF(2) elimination) and `techniques/sequences-dp-search.md` (sum over subsets DP).

## Combinations

The best solution often connects two techniques, especially when a problem has two dimensions (order and lookup, range and count). A combination inherits the "Valid when" conditions of every row it combines; the column below adds only what the combination needs. Combinations with their own row above (difference array, monotonic deque for window extremes, patience sorting) are not repeated.

| Combination | Solves | Valid when | Result |
|---|---|---|---|
| Hash map + prefix sum | Count or find subarrays with a given sum, values of any sign | Prefix sums cannot overflow; exact equality (not floating point) | O(n²) → O(n) expected |
| Hash map + prefix XOR | Count subarrays with a given XOR | Fixed-width integers | O(n²) → O(n) expected |
| Sort + two pointers | Pair/triple sums, closest pairs, merging | Output does not depend on the original order, or indices are kept and restored; duplicates and ties as the original | O(n²) or O(n³) → O(n log n) or O(n²) |
| Sort + binary search | Many lookups against a fixed collection when hashing is not possible (ranges, nearest value) | Collection unchanged between lookups; one comparator for sort and search | O(n·m) → O((n + m) log n) |
| Binary search + monotonic predicate (often a greedy check) | Minimize the maximum, minimum feasible capacity, splitting into groups | Predicate proved monotonic over the whole range; the greedy check itself proved (exchange argument) | O(range · check) → O(log range · check) |
| Heap + hash map | LFU caches, Dijkstra with decrease-key, top-k frequent | Stale heap entries skipped on pop, or decrease-key supported; ties among equal priorities as the original | O(n) operations → O(log n) |
| Monotonic deque + DP | DP whose transition takes the min or max over a sliding window of earlier states | The window is contiguous and its bounds only move forward | O(n·k) → O(n) |
| Sort + union-find | Kruskal MST; offline connectivity under edge-weight thresholds | All queries known up front; ties among equal weights as the original | Repeated traversal → O(E log E) |
| Trie + DFS | Word search in a grid, prefix enumeration | Trie memory bounded when untrusted parties supply words; result order matches when observable | Per-word search → shared prefix search |
| DP + bitmask | Small-set assignment and ordering problems | n bounded in code so 2^n · n fits memory | Factorial → exponential with small base |
| Prefix sums + binary search | Weighted random choice, "first index where the cumulative total exceeds x" | Weights non-negative, enforced in code (a negative weight breaks monotonicity and the search returns an arbitrary index); zero-weight items never chosen, as in the original (left versus right bisection decides); total cannot overflow | O(n) per query → O(log n) |
| Hash map + doubly linked list | O(1) ordered cache with eviction (LRU) | The conditions of the LRU row (key, scope, invalidation, bound) | Bounded memory, O(1) expected operations |
| Sweep line + heap | Meeting rooms, skyline, interval scheduling with resources | Tie order of start and end events, and endpoint semantics, match | O(n²) → O(n log n) |
| Coordinate compression + Fenwick tree | Counting inversions, rank queries over large value ranges (compression keeps order and equality, not distances) | All values known up front; the count type cannot overflow (n² pairs) | O(n²) → O(n log n) |
| Coordinate compression + segment tree | Changing rank and range queries over large values | All values known up front, or rebuilt when new ones arrive | Avoids structures indexed by raw values |
| Sweep line + coordinate compression + Fenwick tree | Counting overlaps, inversions, or active values | As the two rows above; interval endpoints as the original | O(n²) → O(n log n) |

More combinations: "Combinations" in `techniques/sequences-dp-search.md` (meet-in-the-middle) and `techniques/strings-and-text.md` (Aho-Corasick with DP), and the "Trees" table in `techniques/graphs-and-trees.md` (Euler tour with a range structure, rerooting, heavy-light decomposition).
