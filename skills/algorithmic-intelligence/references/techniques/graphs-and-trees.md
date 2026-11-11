# Graphs and Trees

The shared rules and table conventions in `ADVANCED-TECHNIQUES.md` apply to every table here.

## Graphs

Record from the code whether the graph can be disconnected or empty, have cycles, self-loops, parallel edges, or negative weights, and what the original returns for an unreachable node (infinity, −1, a missing key, an error). Three costs are controlled by input:
- **Depth.** Recursive DFS (Tarjan, low-link, tree DP, Euler tours) recurses once per node on a path-shaped graph, exhausting the stack at about 10³ frames in Python (its default recursion limit) and around 10⁴ to 10⁵ in most compiled languages, fewer in worker threads with small stacks. Use an explicit stack when the shape comes from input.
- **Sums.** An "infinity" sentinel plus an edge weight can overflow and wrap to a small value: skip unreachable nodes, or pick a sentinel that leaves room for the longest path.
- **Size.** Node and edge counts from input decide memory (a V × V matrix for Floyd-Warshall is 80 GB at V = 10⁵ with 8-byte entries): cap them ("Algorithmic complexity attacks" in `techniques/hostile-inputs.md`).

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Shortest paths with negative edge weights | Bellman-Ford | No negative cycles reachable, or the code must detect them (Bellman-Ford can) | Handles cases Dijkstra cannot; O(V·E) |
| All-pairs shortest paths, negative edges, sparse graph | Johnson's algorithm (Bellman-Ford reweighting + Dijkstra from each node) | No negative cycles | O(V·E log V) |
| All-pairs shortest paths on a small or dense graph | Floyd-Warshall | Wins over V single-source runs when E is close to V² or V is small. A negative cycle shows as a negative diagonal entry, and entries near it keep decreasing and can overflow; an "infinity" sentinel plus a negative edge looks like a real distance, so skip sentinel entries and check the diagonal as the original does | O(V³), simple, cache-friendly |
| Path search in a very large state space with a good estimate of remaining cost | A* | The heuristic is admissible (never overestimates) for optimal paths; consistent to avoid reopening nodes | Explores far fewer states than Dijkstra in practice; same worst case with a consistent heuristic (an admissible but inconsistent one can reopen nodes exponentially often) |
| Path between two known endpoints in a huge, uniform search space | Bidirectional BFS | Edges can be traversed backward | O(b^d) → O(b^(d/2)) for branching factor b and depth d |
| Strongly connected components, condensing cycles | Tarjan or Kosaraju | — | O(V + E) |
| Critical links or single points of failure | Bridges and articulation points via low-link DFS | Undirected graph; with parallel edges, skip only the edge the DFS arrived by (its id), not every edge back to the parent, or a doubled edge is wrongly reported as a bridge | O(V + E) |
| Longest path or DP over dependencies | DP in topological order | Graph is a DAG, or a cycle in the input is detected and reported the way the original reports it | Exponential path enumeration → O(V + E) |
| Two-coloring, conflict detection | Bipartite check with BFS coloring | A BFS started from every uncolored node, or a disconnected graph is only partly checked | O(V + E) |
| Who-can-do-what assignment (maximum matching) or maximum flow; for minimum-cost assignment see `techniques/optimization-and-scheduling.md` | Hopcroft-Karp (bipartite matching); Dinic or Edmonds-Karp (max flow) | Problem reduces to flow or bipartite matching | Brute force → O(E√V) for matching; O(V²·E) Dinic |
| Many distance or ancestor queries on a tree | Lowest common ancestor via binary lifting, or Euler tour + range-minimum query | Tree does not change between queries | O(n) per query → O(log n), or O(1) with Euler tour + sparse table, after preprocessing |
| Connectivity that changes offline with threshold queries | Sort edges and queries + union-find | All queries known up front | Repeated traversal → O((E + Q) log(E + Q)) |

### Choosing a representation

Pick the representation from what the algorithm asks of the graph most often, and from its density. Changing it can reorder neighbors, which changes which path, spanning tree, or topological order a traversal finds, so keep neighbor order wherever that is observable. Matrices and per-node sets collapse parallel edges, and an undirected graph stored in both directions counts each edge twice.

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Neighbors found by scanning every edge during a traversal | Adjacency list built once: an array of neighbor lists indexed by node | Neighbor order matches the original's edge order where observable | O(V·E) → O(V + E) per traversal; O(V + E) space |
| Frequent "is there an edge from u to v" on a sparse graph | A hash set per node, or sorted neighbor lists with binary search | A set needs a count, or a list of edges, if parallel edges matter; sorting neighbors changes their order | Edge test O(degree) → O(1) expected, or O(log degree) |
| Dense graph (E close to V²), or small V with many edge tests | Adjacency matrix; a bit matrix when unweighted | V² entries fit the memory available ("Size" above) | Edge test O(1); neighbors O(V); O(V²) space, or V²/8 bytes as bits; neighbor-set intersections O(V / word size) |
| Large graph that does not change, dominated by traversal | Compressed sparse row: one array of edges, and one of offsets into it per node | Built once or rebuilt in batches, since one edge update costs up to O(V + E) | Same bounds as an adjacency list; less memory and far fewer cache misses |
| The algorithm walks all edges rather than a node's neighbors (Kruskal, Bellman-Ford) | Edge list | Nothing asks for one node's neighbors | O(E) space, no index to maintain |
| Nodes keyed by strings or objects, with maps of maps | Map keys to dense integers once, then use array-based structures | Output maps back to the original keys; the numbering does not change an observable order | One hash per edge visited removed; a constant factor |

### Changing graphs

A static-graph algorithm rerun after every change costs its full price per change. When the graph changes often between queries (build systems, package managers, schedulers, incremental compilers), count the total cost over the sequence of changes.

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Topological order recomputed after each added edge | Incremental topological ordering (Pearce-Kelly, or Bender-Fineman-Gilbert-Tarjan) | Edges are mostly added; a new edge that closes a cycle is detected and reported the same way the original reports it | O(V + E) re-sort per insertion → work proportional to the region of the order that must shift. A single insertion is no better than re-sorting in the worst case, but m insertions total O(m · min(√m, V^(2/3))) for Bender-Fineman-Gilbert-Tarjan against O(m · (V + E)) for re-sorting each time |
| Unions that must be undone in last-in, first-out order (backtracking search, versioned state) | Union-find with rollback: union by rank or size, a stack of changes, and no path compression | Undo order is last-in, first-out | Rebuild per undo → O(log n) per union, find, and undo |
| Connectivity queries interleaved with edge additions and deletions, all known up front | Offline dynamic connectivity: segment tree over time, each edge inserted into the intervals where it exists, DFS with rollback union-find | All operations known in advance | O(V + E) per query → O((E + Q) log Q log V) total |
| Connectivity queries with online edge additions and deletions | Fully dynamic connectivity (Holm-de Lichtenberg-Thorup) | Large, subtle implementation: prefer a reviewed library (rule 7) | O(V + E) per query → O(log² V) amortized per update, O(log V / log log V) per query |
| Path queries or updates (maximum, sum, add along a path) on a forest whose edges are linked and cut over time | Link-cut trees (Sleator-Tarjan dynamic trees) | The graph stays a forest; aggregates are associative | O(n) per operation → O(log n) amortized; Dinic's max flow with them runs in O(V·E log V) |
| Derived values or reachability over a dependency graph, recomputed in full after a small change | Incremental recomputation: mark changed nodes dirty, recompute only nodes reachable from them in topological order, and stop propagating when a recomputed value is unchanged (early cutoff) | Every dependency edge is tracked; each node's computation is pure | O(V + E) per change → proportional to the affected subgraph |

### Compiler analyses

A faster program analysis must reach the same fixed point, or the compiler's output changes.

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Dataflow analysis (liveness, reaching definitions, available expressions) that sweeps every block until nothing changes | Worklist algorithm that revisits only blocks whose inputs changed, seeded in reverse postorder for forward problems and postorder for backward ones; sets as bit vectors | The transfer functions are monotone over a finite lattice, so the same fixed point is reached | Far fewer block visits; each set operation O(variables / word size) |
| Analyses rerun per variable over the whole control-flow graph | Static single assignment (SSA) form, then sparse analyses along def-use chains | SSA construction and destruction preserve semantics; the analysis is reformulated for SSA | O(blocks × variables) → proportional to the SSA program size |
| Dominators computed by repeated set intersection | Iterative algorithm over reverse postorder (Cooper, Harvey, and Kennedy), or Lengauer-Tarjan | Same dominator tree | Lengauer-Tarjan O(E α(E, V)); the iterative algorithm is often faster on real control-flow graphs |
| Register allocation by graph coloring too slow for the compile-time budget (JIT and fast-compile modes) | Linear-scan allocation over live intervals | Generated code changes (different spills and moves) though its semantics stay the same; measure the generated code's speed as well | Coloring with iterated coalescing → O(n log n) in the number of live intervals |

## Trees

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Subtree sums, counts, or updates | Euler tour (flatten the tree to a range) + Fenwick or segment tree | The tree's shape does not change between queries (values may); the aggregate is associative for a segment tree, and also invertible (sum, count, XOR; not min or max) for a Fenwick tree | O(subtree size) per query → O(log n) |
| An answer computed for every possible root | Tree DP with rerooting | The per-root answer can be combined from child and parent contributions | O(n²) → O(n) |
| Path queries and updates between arbitrary nodes | Heavy-light decomposition + segment tree | Tree shape does not change | O(n) per query → O(log² n) |
| Distance-based counting over all pairs of nodes | Centroid decomposition | — | O(n²) → O(n log n) or O(n log² n) |
