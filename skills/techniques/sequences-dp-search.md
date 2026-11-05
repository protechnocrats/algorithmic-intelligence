# Sequences, Dynamic Programming, and Search

The shared rules and table conventions in `ADVANCED-TECHNIQUES.md` apply.

**Contents:** Sequences and ranges · Dynamic programming optimizations · Combinatorial search · Enumeration and random generation · After NP-hardness · Combinations · References

## Sequences and ranges

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Many offline range queries with no updates, where adding or removing one element updates the answer cheaply | Mo's algorithm | All queries known up front; add/remove are O(1) | O(n·q) → O((n + q)·√n) |
| Range queries and updates with a structure too complex for a segment tree | Square-root decomposition | — | O(n) per operation → O(√n) |
| Queries against past versions of an array | Persistent segment tree | Memory grows by O(log n) per update for as long as versions are kept: bounded by a version limit or released versions (rule 1) | Copying per version → O(log n) per update and query |
| Counting inversions | Merge sort with counting | — | O(n²) → O(n log n) |

## Dynamic programming optimizations

Size the table and its values first. A table dimensioned by an input value (a capacity, a sum) is as large as that value: cap it before allocating. Counting DPs overflow 64 bits quickly (2⁶⁴ subsets of 64 items): keep the original's type, modulus, or big integers. Memoized recursion goes as deep as the longest chain of states (the bottom-up DP row in `CORE-TECHNIQUES.md`).

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| DP transition takes the min/max over a sliding range of previous states | Monotonic deque | The range of candidate states slides monotonically; among equal values, the deque keeps the same state the original picks (pop on ties or not, to match) | O(n·k) → O(n) amortized total |
| Transition minimizes a linear function of earlier states (dp[j] + a[i]·b[j]) | Convex hull trick or Li Chao tree | The transition has that exact linear form; line intersections compared by cross-multiplication in a type wide enough for the products, not by division in floating point | O(n²) → O(n log n), or O(n) with monotonic slopes and queries |
| Optimal split point moves monotonically as i grows | Divide-and-conquer optimization | Monotonicity of the optimal split point is proven | O(k·n²) → O(k·n log n) |
| Interval DP where cost satisfies the quadrangle inequality | Knuth optimization | Quadrangle inequality and monotonicity hold | O(n³) → O(n²) |
| Optimal segmentation or partitioning | Interval DP, partition DP, prefix DP | — | Exhaustive partition enumeration → O(states × transitions per state), often O(n²) or O(n³) |
| Counts or properties of every number in a huge range, digit by digit | Digit DP | Property decomposes over digits | O(range) → O(digits · states) |
| Aggregating over all subsets of each mask | Sum over subsets (SOS) DP | — | O(3^n) → O(n·2^n) |

## Combinatorial search

Everything here keeps an exponential worst case that an adversary or an unlucky instance can reach. With untrusted input or a deadline, cap the instance size and the search (nodes or time), and agree with the developer what a capped search returns (`techniques/hostile-inputs.md`).

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Subset search with n roughly 30 to 45 | Meet-in-the-middle with sorting or hashing | The problem splits into two halves whose results combine; O(2^(n/2)) memory fits | O(2^n) → roughly O(2^(n/2) · n) |
| Search with a strong bound on the best possible remaining result | Branch and bound | The bound is valid (never prunes the optimum) | Large practical speedups; worst case exponential |
| Constraint satisfaction (scheduling, configuration, puzzles) | Constraint propagation with backtracking; most-constrained-variable ordering | Propagation rules are sound | Large practical speedups; worst case exponential |
| Repeated states in a search | Memoize states in a hash set | State has a canonical, hashable form; memory grows with every distinct state, so bound it | Repeated subtrees → explored once |
| Deep search where memory for BFS is too large | Iterative deepening (IDDFS, IDA*) | Steps have unit cost (IDA* for varied costs); repeating the shallow levels is acceptable, which holds when the tree grows geometrically; the order in which solutions are found matches, if observable | Same time order as BFS with O(depth) memory |
| Exact cover (Sudoku, tiling, polyomino puzzles, some scheduling and configuration problems) solved by backtracking that copies or rescans the remaining choices | Knuth's Algorithm X with Dancing Links: circular doubly linked lists make removing and restoring a choice O(1) per link; branch on the column with the fewest remaining rows | A true exact cover (optional columns allowed); if callers see which solution comes first, or the order of all solutions, the branching order matches the original's | Same exponential worst case, with undo in O(1) per link instead of copying state; large practical speedups |

## Enumeration and random generation

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Shuffling by sorting with a random comparator (`sort(() => Math.random() - 0.5)`), or by repeatedly removing a random element from a list | Fisher-Yates shuffle (Knuth's Algorithm P): swap each position with a random position at or before it | Behavior change: the random comparator is biased (which orders are favored depends on the sort), so a correct shuffle gives a different distribution, and seeded sequences change. Draw each index uniformly (`rand() % n` is biased); a generator with less state than log₂(n!) bits cannot reach every permutation (52 cards need about 226 bits); a shuffle that decides money or security needs a cryptographically secure generator | O(n log n) or O(n²) → O(n), with every permutation equally likely |
| Enumerating all subsets and re-scoring each from scratch | Gray-code order: consecutive subsets differ by one element (binary reflected Gray code), so the score is updated by adding or removing one element | The score can be updated incrementally; behavior change if callers see the enumeration order | O(n · 2^n) → O(2^n) plus one update per step |
| Enumerating all k-element combinations and re-scoring each | Revolving-door order (each combination differs from the previous by swapping one element in and one out) | Incremental score update; enumeration order matches or is not observable | O(k) per combination → one swap update |
| Enumerating all permutations and re-scoring each | Heap's algorithm or Steinhaus-Johnson-Trotter (each permutation differs from the previous by one swap or one adjacent swap), with an incremental score update; Knuth's Algorithm L when lexicographic order is required | Order matches the original's (lexicographic only with Algorithm L), or is not observable | O(n) work per permutation → O(1) amortized generation plus one swap update (Algorithm L: a swap plus a suffix reversal, O(1) amortized element changes) |

## After NP-hardness

A reduction from a known NP-hard problem (move 6 in `DISCOVERY.md`) means no known algorithm is polynomial on every input, not that the code's instances are hard. Try these in order and report which applies:

1. **Exploitable structure**, measured on real data: small integer weights or capacities (pseudo-polynomial DP), a small parameter k such as solution size or distinct values (an algorithm exponential only in k, such as O(2^k · n)), a tree or low-treewidth graph (DP over the tree decomposition), few distinct items (group them), or a polynomial special case (`techniques/optimization-and-scheduling.md`).
2. **Faster exact search**: branch and bound, constraint propagation, meet-in-the-middle, memoized states, or an integer-programming or SAT solver (rule 7). The worst case stays exponential; record the measured sizes that stay within budget.
3. **An approximation with a proven ratio** (first-fit decreasing, greedy set cover), if the developer accepts it: a behavior change.
4. **A heuristic with no guarantee** (local search, simulated annealing), with measured quality against a lower bound or known optima on real instances: a behavior change, often nondeterministic, so fix the seed if the original was deterministic.

## Combinations

| Combination | Solves | Result |
|---|---|---|
| Meet-in-the-middle + hashing or sorting | Subset sum, balanced partition for medium n | O(2^n) → roughly O(2^(n/2) · n) |
| Gray-code enumeration + incremental scoring | Exhaustive search over subsets where each step changes one element | O(n · 2^n) → O(2^n) |

## References

Sources: `references/techniques/sequences-dp-search.md`, read only to verify a claim.
