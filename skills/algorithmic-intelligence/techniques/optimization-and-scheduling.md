# Optimization, Scheduling, and Allocation

Part of the advanced techniques. The shared rules in `ADVANCED-TECHNIQUES.md` apply to every table in this file; read them first. Tables are read as described there.

For code that searches for the best assignment, schedule, route, packing, or allocation: job and task schedulers (operating systems, build systems, batch and cluster schedulers), compilers (instruction scheduling, register and memory allocation), query optimizers, logistics and routing, timetabling, ad and resource allocation, and capacity planning. The usual slow form is a loop over permutations, subsets, or candidate plans. Sometimes the fastest fix is not a faster loop but a better formulation of the problem.

## Before choosing

1. **Write the model.** Name the decision variables, the constraints, and the objective. Most code that searches for a "best" plan never states them, and many recognizable problems appear once they are written down.
2. **Check for a polynomial special case** (first table). Many scheduling and assignment problems that look combinatorial have exact greedy or flow solutions.
3. **Only then treat it as hard.** If the problem is NP-hard in general (move 6 in `DISCOVERY.md`), see "After NP-hardness" in `techniques/sequences-dp-search.md` for the options: structure that makes the instances easy, approximation with a guarantee, a solver, or a heuristic.

**Exact versus not exact.** If the original returns a provably optimal answer, anything that may return a different answer is a behavior change (rule 5): heuristics, approximation algorithms, solvers stopped by a time limit, and solvers that return a different optimal solution among several equally good ones. Ties between optimal solutions are common in scheduling and assignment, and callers often observe which one they get. State the tie-breaking rule of the original and reproduce it, or list the change for review.

## Polynomial special cases

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Assigning n workers to n jobs at minimum total cost by trying permutations | Hungarian algorithm, or min-cost bipartite matching | One worker per job; costs additive; rectangular cases padded | O(n!) → O(n³) |
| Shipping supply to demand at minimum cost, or any assignment with capacities | Min-cost flow (transportation problem) | Costs linear in the amounts; integer capacities give integer optimal solutions | Exponential search → polynomial; network-simplex solvers are fast in practice |
| An integer program whose constraint matrix is a network or bipartite incidence matrix | Solve it as a linear program or a flow: totally unimodular constraints have integer optimal solutions at the vertices | The matrix is totally unimodular (flows, bipartite matching, interval constraints with consecutive ones) | NP-hard in general → polynomial |
| Choosing a subset of projects with prerequisites to maximize profit | Maximum-weight closure via minimum cut | Prerequisites form a directed graph; profits and costs additive | Exponential subsets → one max-flow computation |
| Greedy selection by weight (choose the most valuable items subject to independence rules) | Prove the feasible sets form a matroid (forests in a graph, linearly independent sets, sets with at most k from each group); then greedy by weight is optimal | The exchange property holds; it fails for knapsack-like capacity limits | Exponential → O(n log n) plus independence checks |
| One machine, minimize average or weighted completion time | Shortest processing time first; Smith's rule (sort by processing time divided by weight) for weights | Jobs available at time zero, no preemption | O(n!) → O(n log n) |
| One machine, minimize the maximum lateness | Earliest due date first (Jackson's rule) | Jobs available at time zero | O(n!) → O(n log n) |
| One machine, minimize the number of late jobs | Moore-Hodgson algorithm | Unweighted jobs, available at time zero | O(2^n) → O(n log n) |
| Preemptive real-time tasks on one processor | Earliest deadline first | Preemption allowed; periodic tasks with deadlines equal to their periods; context-switch cost negligible or modeled | Schedulable whenever total utilization ≤ 1 |
| Two machines in sequence (flow shop), minimize total completion of the batch (makespan) | Johnson's rule | Exactly two machines, same job order on both | O(n!) → O(n log n) |
| Choose the most non-overlapping time slots; or weighted slots | Earliest finish time first; weighted interval scheduling by DP with binary search | Intervals known up front | O(2^n) → O(n log n) |
| Distributing a budget of units among activities with diminishing returns | Greedy by marginal gain, one unit at a time or by a heap | Each activity's return is concave in its units and the objective is their sum | Exponential combinations → O(B log n) for B units, or faster by binary search on the marginal value |

## Modeling and solvers

When no special case fits and the instances are large or the constraints change often, a declarative model handed to a solver usually beats custom search code, both in speed and in what it can express. Solvers are dependencies: ask first (rule 7), and check licenses (several commercial solvers need paid licenses; OR-Tools, HiGHS, and CBC are open source).

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Continuous decisions with linear constraints and a linear objective (blending, flows, budgets) | Linear programming (simplex, interior-point methods) | The model is truly linear; floating-point tolerances accepted; when several optima exist, which one is returned may change (behavior change if observable) | Polynomial time (interior point); simplex is exponential in the worst case but fast in practice |
| Yes-or-no or integer decisions with linear constraints (selection, assignment with side rules, routing) | Integer or mixed-integer programming (branch and cut) | Problem sizes measured; a time limit yields a feasible answer with a reported optimality gap, which is a behavior change unless the original also stopped early | NP-hard in general; modern solvers handle large real instances |
| Scheduling or configuration with many logical rules (precedence, calendars, no-overlap, "at most k of these") | Constraint programming with global constraints (no-overlap, cumulative, all-different) and search strategies | Every rule encoded; the solution chosen among equals may differ from the original's | Large practical reductions over hand-written backtracking |
| Pure boolean constraints | A SAT solver; 2-SAT in linear time when every clause has two literals | Encoding verified on known instances | Exponential worst case; conflict-driven solvers handle millions of clauses in practice |
| The same optimization re-solved from scratch after small changes (new orders, a machine down) | Warm-start the solver from the previous solution; rolling-horizon re-optimization over a window | Re-planning may move already-announced work: decide which decisions are frozen | Solve time proportional to the change, in practice |

## Heuristics with guarantees

Use these only when exact answers are too slow for the measured sizes, and list them as behavior changes unless the original was already a heuristic. Prefer ones with a proven worst-case ratio, and state it.

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Bin packing (containers, memory pages, batches) by exhaustive search | First-fit decreasing | Approximate packing accepted | At most 11/9 of the optimal bin count plus 6/9; O(n log n) |
| Spreading jobs over identical machines to minimize the finishing time of the last one | Longest processing time first | Approximate accepted | At most 4/3 − 1/(3m) of optimal for m machines; O(n log n) |
| Covering every element with the fewest sets | Greedy by most new elements covered | Approximate accepted | Within a factor of about ln n of optimal; essentially the best possible in polynomial time unless P = NP |
| Knapsack with large capacities where the pseudo-polynomial DP table is too big | Fully polynomial approximation scheme: scale and round values, then DP | A stated tolerance ε | Within (1 − ε) of optimal in time polynomial in n and 1/ε |
| Traveling salesperson or vehicle routing beyond the size bitmask DP can handle | Construction heuristics (Christofides within 1.5 of optimal on metric distances; savings algorithm for vehicle routing), then local search (2-opt, Or-opt, relocate and exchange moves) | Approximate routes accepted; metric distances for Christofides' guarantee | Large instances solved in seconds; quality measured against lower bounds or known optima |

## Several objectives

When the code trades off several goals (cost and time, latency and throughput), first decide how they combine:

- **Lexicographic:** optimize the first objective, then the second among the solutions that tie on the first. Reproduces "sort by A, then B" rules exactly.
- **Weighted sum:** one combined score. It finds only solutions on the convex part of the trade-off curve.
- **Pareto front:** keep every solution that no other solution beats on all objectives, and let the caller choose. Computing the front of n points is O(n log n) in two or three dimensions (sort by one objective, then sweep), instead of comparing all O(n²) pairs.

Changing how objectives combine changes which solution is chosen: a behavior change.

## Decisions without the future (online algorithms)

Many systems decisions must be made before the future is known: whether to keep spinning or block, whether to build an index or keep scanning, which cache entry to evict, which machine gets the next job. Online algorithms make these decisions with a proven guarantee against the best choice made with hindsight (the competitive ratio). Several rows elsewhere in this skill are instances; this section gives their reasoning.

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Paying a repeated cost or a one-time cost without knowing how often the need recurs: spin or block (adaptive locks), scan or build an index, recompute or cache, interpret or compile (JIT tiers), reconnect or keep a connection | Ski rental: keep paying the repeated cost until it adds up to the one-time cost, then pay the one-time cost | The two costs are measured; changing the threshold changes timing, not results | Never more than twice the hindsight-optimal cost (deterministic); about 1.58 times with a randomized threshold |
| Choosing a cache eviction policy and judging how good it is | Compare against Belady's optimal policy (evict the item used furthest in the future), computed offline on a recorded access trace; LRU and FIFO are k-competitive for a cache of k items | A representative trace is available; see "Caching and eviction" in `techniques/data-structures.md` for the policies | Shows how much hit rate any policy could still gain on this workload |
| Jobs arriving one at a time must be assigned to identical machines | List scheduling: assign each job to the least-loaded machine (a heap of loads) | Jobs cannot be reassigned later; if all jobs are known first, sort them longest first ("Heuristics with guarantees") | Within 2 − 1/m of the optimal finishing time for m machines; O(log m) per job |
| Items arriving one at a time must be packed into bins | First fit (place in the first bin with room) | Approximate packing accepted; if all items are known first, use first-fit decreasing | At most 1.7 times the optimal number of bins |

## References (for verifying claims; not required reading)

- Jon Kleinberg and Éva Tardos, *Algorithm Design* (2005): greedy algorithms, network flow.
- Michael L. Pinedo, *Scheduling: Theory, Algorithms, and Systems*, 6th ed. (2022).
- David P. Williamson and David B. Shmoys, *The Design of Approximation Algorithms* (2011).
- Allan Borodin and Ran El-Yaniv, *Online Computation and Competitive Analysis* (1998); Daniel D. Sleator and Robert E. Tarjan, "Amortized Efficiency of List Update and Paging Rules," *CACM* 28(2), 1985; R. L. Graham, "Bounds for Certain Multiprocessing Anomalies" (1966).
- Alexander Schrijver, *Theory of Linear and Integer Programming* (1986).
