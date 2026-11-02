# Sequences, Dynamic Programming, and Search

Part of the advanced techniques. The shared rules in `ADVANCED-TECHNIQUES.md` apply to every table in this file; read them first. Tables are read as described there.

## Sequences and ranges

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Many offline range queries with no updates, where adding or removing one element updates the answer cheaply | Mo's algorithm | All queries known up front; add/remove are O(1) | O(n·q) → O((n + q)·√n) |
| Range queries and updates with a structure too complex for a segment tree | Square-root decomposition | — | O(n) per operation → O(√n) |
| Queries against past versions of an array | Persistent segment tree | Memory grows by O(log n) per update for as long as versions are kept: bounded by a version limit or released versions (rule 1) | Copying per version → O(log n) per update and query |
| Counting inversions | Merge sort with counting | — | O(n²) → O(n log n) |

## Dynamic programming optimizations

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| DP transition takes the min/max over a sliding range of previous states | Monotonic deque | The range of candidate states slides monotonically | O(n·k) → O(n) amortized total |
| Transition minimizes a linear function of earlier states (dp[j] + a[i]·b[j]) | Convex hull trick or Li Chao tree | The transition has that exact linear form | O(n²) → O(n log n), or O(n) with monotonic slopes and queries |
| Optimal split point moves monotonically as i grows | Divide-and-conquer optimization | Monotonicity of the optimal split point is proven | O(k·n²) → O(k·n log n) |
| Interval DP where cost satisfies the quadrangle inequality | Knuth optimization | Quadrangle inequality and monotonicity hold | O(n³) → O(n²) |
| Optimal segmentation or partitioning | Interval DP, partition DP, prefix DP | — | Exhaustive partition enumeration → O(states × transitions per state), often O(n²) or O(n³) |
| Counts or properties of every number in a huge range, digit by digit | Digit DP | Property decomposes over digits | O(range) → O(digits · states) |
| Aggregating over all subsets of each mask | Sum over subsets (SOS) DP | — | O(3^n) → O(n·2^n) |

## Combinatorial search

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Subset search with n roughly 30 to 45 | Meet-in-the-middle with sorting or hashing | The problem splits into two halves whose results combine | O(2^n) → roughly O(2^(n/2) · n) |
| Search with a strong bound on the best possible remaining result | Branch and bound | The bound is valid (never prunes the optimum) | Large practical speedups; worst case exponential |
| Constraint satisfaction (scheduling, configuration, puzzles) | Constraint propagation with backtracking; most-constrained-variable ordering | Propagation rules are sound | Large practical speedups; worst case exponential |
| Repeated states in a search | Memoize states in a hash set | State has a canonical, hashable form | Repeated subtrees → explored once |
| Deep search where memory for BFS is too large | Iterative deepening (IDDFS, IDA*) | Steps have unit cost (IDA* for varied costs); repeating the shallow levels is acceptable, which holds when the tree grows geometrically; the order solutions are found in matches if observable | Same time order as BFS with O(depth) memory |
| Exact cover: choose rows so every column is covered exactly once (Sudoku, tiling, polyomino and pentomino puzzles, some scheduling and configuration problems), solved by backtracking that copies or rescans the remaining choices | Knuth's Algorithm X with Dancing Links: columns and rows in circular doubly linked lists, so removing and restoring a choice is O(1) per link; always branch on the column with the fewest remaining rows | The problem is a true exact cover (or exact cover with optional columns); if callers see which solution comes first, or the order of all solutions, the branching order must match the original's | Same exponential worst case, with undo in O(1) per link instead of copying state; large practical speedups |

## Enumeration and random generation

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Shuffling by sorting with a random comparator (`sort(() => Math.random() - 0.5)`), or by repeatedly removing a random element from a list | Fisher-Yates shuffle (Knuth's Algorithm P): swap each position with a random position at or before it | **Behavior change**: the random comparator is also biased (some orders are more likely than others, depending on the sort algorithm), so a correct shuffle produces a different distribution; and any shuffle draws random numbers differently, so seeded sequences change | O(n log n) or O(n²) → O(n), with every permutation equally likely |
| Enumerating all subsets and re-scoring each one from scratch | Gray-code order: consecutive subsets differ by one element (binary reflected Gray code), so the score is updated by adding or removing one element | The score can be updated incrementally; **behavior change** if callers see the enumeration order | O(n · 2^n) → O(2^n) plus one update per step |
| Enumerating all k-element combinations and re-scoring each | Revolving-door order (each combination differs from the previous by swapping one element in and one out) | Incremental score update; enumeration order matches or is not observable | O(k) per combination → one swap update |
| Enumerating all permutations and re-scoring each one | Heap's algorithm or Steinhaus-Johnson-Trotter (each permutation differs from the previous by one swap or one adjacent swap), with an incremental score update; Knuth's Algorithm L when lexicographic order is required | Order matches the original's (lexicographic only with Algorithm L), or is not observable | O(n) work per permutation → O(1) amortized generation plus one swap update |

## After NP-hardness

A reduction from a known NP-hard problem (move 6 in `DISCOVERY.md`) means no algorithm is known that is polynomial on every input. It does not mean the code's instances are hard. Work through these in order, and report which applies:

1. **Instances have exploitable structure.** Small integer weights or capacities (pseudo-polynomial DP), a small parameter k such as solution size or number of distinct values (a parameterized algorithm exponential only in k, such as O(2^k · n)), a tree or low-treewidth graph (DP over the tree decomposition), few distinct items (group them), or a special case that is polynomial (see `techniques/optimization-and-scheduling.md`). Measure the parameter on real data.
2. **Exact search can be made much faster** without giving up optimality: branch and bound with a strong bound, constraint propagation, meet-in-the-middle, memoized states, or an integer-programming or SAT solver (a dependency, rule 7). The worst case stays exponential; record the measured sizes where it stays within budget.
3. **An approximation with a proven ratio** is acceptable to the developer: state the ratio, for example first-fit decreasing for bin packing or the greedy set cover. A behavior change (rule 5).
4. **A heuristic with no guarantee** (local search, simulated annealing, genetic algorithms) is acceptable: report its measured quality against a lower bound or known optima on real instances. A behavior change (rule 5), and often nondeterministic: fix the seed if the original was deterministic.

## Combinations

| Combination | Solves | Result |
|---|---|---|
| Meet-in-the-middle + hashing or sorting | Subset sum, balanced partition for medium n | O(2^n) → roughly O(2^(n/2) · n) |
| Gray-code enumeration + incremental scoring | Exhaustive search over subsets where each step changes one element | O(n · 2^n) → O(2^n) |

## References (for verifying claims; not required reading)

- Cormen, Leiserson, Rivest, and Stein, *Introduction to Algorithms*, 4th ed. (2022): dynamic programming, NP-completeness, approximation algorithms.
- Marek Cygan et al., *Parameterized Algorithms* (2015).
- Donald E. Knuth, "Dancing Links" (2000), and *The Art of Computer Programming*, Vol. 4A (2011), section 7.2.1 (generating tuples, permutations, and combinations, including Gray codes and Algorithm L), Vol. 2, section 3.4.2 (random permutations, Algorithm P).
- David P. Williamson and David B. Shmoys, *The Design of Approximation Algorithms* (2011).
