# Graphs and Trees

Part of the advanced techniques. The shared rules in `ADVANCED-TECHNIQUES.md` apply to every table in this file; read them first. Tables are read as described there.

## Graphs

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Shortest paths with negative edge weights | Bellman-Ford | No negative cycles reachable, or the code must detect them (Bellman-Ford can) | Handles cases Dijkstra cannot; O(V·E) |
| All-pairs shortest paths, negative edges, sparse graph | Johnson's algorithm (Bellman-Ford reweighting + Dijkstra from each node) | No negative cycles | O(V·E log V) |
| All-pairs shortest paths on a small or dense graph | Floyd-Warshall | Replaces V separate single-source runs; wins when E is close to V² or V is small | O(V³), simple, cache-friendly |
| Path search in a very large state space with a good estimate of remaining cost | A* | The heuristic is admissible (never overestimates) for optimal paths; consistent to avoid reopening nodes | Explores far fewer states than Dijkstra in practice; same worst case with a consistent heuristic (an admissible but inconsistent one can reopen nodes exponentially often) |
| Path between two known endpoints in a huge, uniform search space | Bidirectional BFS | Edges can be traversed backward | O(b^d) → O(b^(d/2)) for branching factor b and depth d |
| Strongly connected components, condensing cycles | Tarjan or Kosaraju | — | O(V + E) |
| Critical links or single points of failure | Bridges and articulation points via low-link DFS | Undirected graph | O(V + E) |
| Longest path or DP over dependencies | DP in topological order | Graph is a DAG | Exponential path enumeration → O(V + E) |
| Two-coloring, conflict detection | Bipartite check with BFS coloring | — | O(V + E) |
| Who-can-do-what assignment (maximum matching) or maximum flow; for minimum-cost assignment see `techniques/optimization-and-scheduling.md` | Hopcroft-Karp (bipartite matching); Dinic or Edmonds-Karp (max flow) | Problem reduces to flow or bipartite matching | Brute force → O(E√V) for matching; O(V²·E) Dinic |
| Many distance or ancestor queries on a tree | Lowest common ancestor via binary lifting, or Euler tour + range-minimum query | Tree does not change between queries | O(n) per query → O(log n), or O(1) with Euler tour + sparse table, after preprocessing |
| Connectivity that changes offline with threshold queries | Sort edges and queries + union-find | All queries known up front | Repeated traversal → O((E + Q) log(E + Q)) |

### Changing graphs

A static-graph algorithm rerun after every change costs its full price per change. When edges or nodes change often between queries (build systems, package managers, schedulers, lock-order checkers, incremental compilers), count the total cost over the sequence of changes.

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Topological order recomputed after each added edge | Incremental topological ordering (Pearce-Kelly, or Bender-Fineman-Gilbert-Tarjan) | Edges are mostly added; a new edge that closes a cycle is detected and reported the same way the original reports it | O(V + E) re-sort per insertion → work proportional to the region of the order that must shift, in practice; worst case for a single insertion is no better than re-sorting, but the total over m insertions is O(m · min(√m, V^(2/3))) for Bender-Fineman-Gilbert-Tarjan, against O(m · (V + E)) for re-sorting each time |
| Unions that must be undone in last-in, first-out order (backtracking search, versioned state) | Union-find with rollback: union by rank or size, **no** path compression, a stack of changes | Undo order is last-in, first-out | Rebuild per undo → O(log n) per union, find, and undo |
| Connectivity queries interleaved with edge additions and deletions, all known up front | Offline dynamic connectivity: segment tree over time, each edge inserted into the intervals where it exists, DFS with rollback union-find | All operations known in advance | O(V + E) per query → O((E + Q) log Q log V) total |
| Connectivity queries with online edge additions and deletions | Fully dynamic connectivity (Holm-de Lichtenberg-Thorup) | Large, subtle implementation: prefer a reviewed library and ask (rule 7) | O(V + E) per query → O(log² V) amortized per update, O(log V / log log V) per query |
| Path queries or updates (maximum, sum, add along a path) on a forest whose edges are linked and cut over time | Link-cut trees (Sleator-Tarjan dynamic trees) | The graph stays a forest; aggregates are associative | O(n) per operation → O(log n) amortized; Dinic's max flow with them runs in O(V·E log V) |
| Derived values or reachability over a dependency graph, recomputed in full after a small change | Incremental recomputation: mark changed nodes dirty, recompute only nodes reachable from them, in topological order; stop propagating when a recomputed value is unchanged (early cutoff) | Every dependency edge is tracked; each node's computation is pure | O(V + E) per change → proportional to the affected subgraph |

### Compiler analyses

Program analyses are graph problems over the control-flow graph. A faster analysis must compute the same result (the same fixed point), or the compiler's output changes.

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Dataflow analysis (liveness, reaching definitions, available expressions) that sweeps every block until nothing changes | Worklist algorithm that revisits only blocks whose inputs changed, seeded in reverse postorder for forward problems and postorder for backward ones; sets as bit vectors | The transfer functions are monotone over a finite lattice, so the same fixed point is reached | Far fewer block visits; each set operation O(variables / word size) |
| Analyses rerun per variable over the whole control-flow graph | Static single assignment (SSA) form, then sparse analyses along def-use chains | SSA construction and destruction preserve semantics; the analysis is reformulated for SSA | O(blocks × variables) → proportional to the SSA program size |
| Dominators computed by repeated set intersection | Iterative algorithm over reverse postorder (Cooper, Harvey, and Kennedy), or Lengauer-Tarjan | Same dominator tree | Lengauer-Tarjan O(E α(E, V)); the iterative algorithm is often faster on real control-flow graphs |
| Register allocation by graph coloring too slow for the compile-time budget (JIT and fast-compile modes) | Linear-scan allocation over live intervals | Generated code changes (different spills and moves): a behavior change in the compiler's output, though the compiled program's semantics stay the same; measure the generated code's speed as well | Coloring with iterated coalescing → O(n log n) in the number of live intervals |

## Trees

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Subtree sums, counts, or updates | Euler tour (flatten the tree to a range) + Fenwick or segment tree | The tree's shape does not change between queries (values may); the aggregate is associative for a segment tree, and also invertible (sum, count, XOR; not min or max) for a Fenwick tree | O(subtree size) per query → O(log n) |
| An answer computed for every possible root | Tree DP with rerooting | The per-root answer can be combined from child and parent contributions | O(n²) → O(n) |
| Path queries and updates between arbitrary nodes | Heavy-light decomposition + segment tree | Tree shape does not change | O(n) per query → O(log² n) |
| Distance-based counting over all pairs of nodes | Centroid decomposition | — | O(n²) → O(n log n) or O(n log² n) |

## References (for verifying claims; not required reading)

- Robert E. Tarjan, *Data Structures and Network Algorithms* (1983).
- Keith D. Cooper and Linda Torczon, *Engineering a Compiler*, 3rd ed. (2022): dataflow analysis, SSA, register allocation.
- Daniel D. Sleator and Robert E. Tarjan, "A Data Structure for Dynamic Trees," *Journal of Computer and System Sciences* 26(3), 1983.
- Keith D. Cooper, Timothy J. Harvey, and Ken Kennedy, "A Simple, Fast Dominance Algorithm" (2001).
- Massimiliano Poletto and Vivek Sarkar, "Linear Scan Register Allocation," *ACM TOPLAS* 21(5), 1999.
