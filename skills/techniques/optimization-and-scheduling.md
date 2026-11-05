# Optimization, Scheduling, and Allocation

The shared rules and table conventions in `ADVANCED-TECHNIQUES.md` apply.

**Contents:** Before choosing · Polynomial special cases · Modeling and solvers · Heuristics with guarantees · Several objectives · Decisions without the future (online algorithms) · References

For code that searches for the best assignment, schedule, route, packing, or allocation (schedulers, compilers, query optimizers, logistics, timetabling, capacity planning). The slow form is usually a loop over permutations, subsets, or candidate plans, and the fix is often a better formulation, not a faster loop.

## Before choosing

1. **Write the model**: decision variables, constraints, objective. Code searching for a "best" plan rarely states them, and a recognizable problem often appears once they are written.
2. **Check for a polynomial special case** (first table): many scheduling and assignment problems that look combinatorial have exact greedy or flow solutions.
3. **Pin down time and intervals.** Record from the code whether ends are inclusive (do [9:00, 10:00] and [10:00, 11:00] conflict), how an interval crossing midnight is stored, local time or UTC (a local day has 23 or 25 hours across a daylight-saving change, and a local time can occur twice or not at all), and whose clock wins when machines disagree. The new code makes each choice the same way; test each.
4. **Only then treat it as hard.** If it is NP-hard in general (move 6 in `DISCOVERY.md`), see "After NP-hardness" in `techniques/sequences-dp-search.md`.

**Exact versus not exact.** If the original returns a provably optimal answer, anything that may return a different one is a behavior change: heuristics, approximations, solvers stopped by a time limit, and solvers returning a different one of several equally good optima. Ties between optima are common in scheduling and assignment, and callers often observe which one they get: reproduce the original's tie-breaking or list the change.

## Polynomial special cases

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Assigning n workers to n jobs at minimum total cost by trying permutations | Hungarian algorithm, or min-cost bipartite matching | One worker per job; costs additive; with n workers and m > n jobs, the rectangular form runs in O(n²·m), while padding to square costs O(m³); forbidden pairs given a large cost that cannot overflow when n of them are summed | O(n!) → O(n³) |
| Shipping supply to demand at minimum cost, or any assignment with capacities | Min-cost flow (transportation problem) | Costs linear in the amounts; integer capacities give integer optimal solutions | Exponential search → polynomial; network-simplex solvers are fast in practice |
| An integer program whose constraint matrix is a network or bipartite incidence matrix | Solve it as a linear program or a flow: totally unimodular constraints have integer optimal solutions at the vertices | The matrix is totally unimodular (flows, bipartite matching, interval constraints with consecutive ones), and the right-hand sides and variable bounds are integers; with fractional data the LP optimum can be fractional | NP-hard in general → polynomial |
| Choosing a subset of projects with prerequisites to maximize profit | Maximum-weight closure via minimum cut | Prerequisites form a directed graph; profits and costs additive | Exponential subsets → one max-flow computation |
| Greedy selection by weight (choose the most valuable items subject to independence rules) | Prove the feasible sets form a matroid (forests in a graph, linearly independent sets, sets with at most k from each group); then greedy by weight is optimal | The exchange property holds; it fails for knapsack-like capacity limits | Exponential → O(n log n) plus independence checks |
| One machine, minimize average or weighted completion time | Shortest processing time first; Smith's rule (sort by processing time divided by weight) for weights | Jobs available at time zero, no preemption; compare ratios by cross-multiplication (p₁·w₂ against p₂·w₁) in a type wide enough for the products, so zero weights do not divide by zero and rounding does not reorder near-equal jobs; an overflowing product makes the comparator inconsistent, which some sorts reject or order wrongly | O(n!) → O(n log n) |
| One machine, minimize the maximum lateness | Earliest due date first (Jackson's rule) | Jobs available at time zero | O(n!) → O(n log n) |
| One machine, minimize the number of late jobs | Moore-Hodgson algorithm | Unweighted jobs, available at time zero | O(2^n) → O(n log n) |
| Preemptive real-time tasks on one processor | Earliest deadline first | Preemption allowed; periodic tasks with deadlines equal to their periods; context-switch cost negligible or modeled | Schedulable whenever total utilization ≤ 1. Above 1, EDF can miss many deadlines in a cascade, where fixed priorities miss only the lowest-priority tasks: keep the original's overload behavior or list the change |
| Two machines in sequence (flow shop), minimize the time the last job finishes (makespan) | Johnson's rule | Exactly two machines, same job order on both | O(n!) → O(n log n) |
| Choose the most non-overlapping time slots; or weighted slots | Earliest finish time first; weighted interval scheduling by DP with binary search | Intervals known up front; touching intervals treated as conflicting or not exactly as the original treats them | O(2^n) → O(n log n) |
| Distributing a budget of units among activities with diminishing returns | Greedy by marginal gain, one unit at a time or by a heap | Each activity's return is concave in its units and the objective is their sum | Exponential combinations → O(B log n) for B units, or faster by binary search on the marginal value |

## Modeling and solvers

When no special case fits and instances are large or constraints change often, a declarative model handed to a solver usually beats custom search code. Solvers are dependencies (rule 7); several commercial ones need paid licenses, while OR-Tools, HiGHS, and CBC are open source. The worst case stays exponential: give every solve a time and memory limit, cap instance sizes from input, and agree with the developer what a limited solve returns. Multithreaded solvers can return a different optimum each run; set their deterministic mode when callers compare results.

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Continuous decisions with linear constraints and a linear objective (blending, flows, budgets) | Linear programming (simplex, interior-point methods) | The model is truly linear; floating-point tolerances accepted; when several optima exist, which one is returned may change (behavior change if observable) | Polynomial time (interior point); simplex is exponential in the worst case but fast in practice |
| Yes-or-no or integer decisions with linear constraints (selection, assignment with side rules, routing) | Integer or mixed-integer programming (branch and cut) | Problem sizes measured; a time limit yields a feasible answer with a reported optimality gap, which is a behavior change unless the original also stopped early. Integer variables come back within a tolerance (0.9999999): round them explicitly | NP-hard in general; modern solvers handle large real instances |
| Scheduling or configuration with many logical rules (precedence, calendars, no-overlap, "at most k of these") | Constraint programming with global constraints (no-overlap, cumulative, all-different) and search strategies | Every rule encoded; the solution chosen among equals may differ from the original's | Large practical reductions over hand-written backtracking |
| Pure boolean constraints | A SAT solver; 2-SAT in linear time when every clause has two literals | Encoding verified on known instances | Exponential worst case; conflict-driven solvers handle millions of clauses in practice |
| The same optimization re-solved from scratch after small changes (new orders, a machine down) | Warm-start the solver from the previous solution; rolling-horizon re-optimization over a window | Re-planning may move already-announced work: decide which decisions are frozen | Solve time proportional to the change, in practice |

## Heuristics with guarantees

Only when exact answers are too slow at the measured sizes; a behavior change unless the original was already a heuristic. State the proven worst-case ratio.

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Bin packing (containers, memory pages, batches) by exhaustive search | First-fit decreasing | Approximate packing accepted | At most 11/9 of the optimal bin count plus 6/9; O(n log n) |
| Spreading jobs over identical machines to minimize the finishing time of the last one | Longest processing time first | Approximate accepted | At most 4/3 − 1/(3m) of optimal for m machines; O(n log n) |
| Covering every element with the fewest sets | Greedy by most new elements covered | Approximate accepted | Within a factor of about ln n of optimal; essentially the best possible in polynomial time unless P = NP |
| Knapsack with large capacities where the pseudo-polynomial DP table is too big | Fully polynomial approximation scheme: scale and round values, then DP | A stated tolerance ε | Within (1 − ε) of optimal in time polynomial in n and 1/ε |
| Traveling salesperson or vehicle routing beyond the size bitmask DP can handle | Construction heuristics (Christofides within 1.5 of optimal on metric distances; savings algorithm for vehicle routing), then local search (2-opt, Or-opt, relocate and exchange moves) | Approximate routes accepted; metric distances for Christofides' guarantee | Large instances solved in seconds; quality measured against lower bounds or known optima |

## Several objectives

When the code trades off several goals (cost and time, latency and throughput), decide how they combine. Changing how existing code combines them changes which solution is chosen: a behavior change.

- **Lexicographic:** optimize the first objective, then the second among solutions tying on the first. Reproduces "sort by A, then B" rules exactly.
- **Weighted sum:** one combined score; finds only solutions on the convex part of the trade-off curve.
- **Pareto front:** keep every solution that no other solution beats on all objectives, and let the caller choose. The front of n points is O(n log n) in two dimensions (sort by one objective, then sweep) and in three (a sweep with a balanced tree), instead of comparing all O(n²) pairs. Match the original on whether two solutions with equal scores both stay.

## Decisions without the future (online algorithms)

Decisions made before the future is known (spin or block, build an index or keep scanning, which entry to evict, which machine gets the next job), with a proven competitive ratio against the best choice in hindsight.

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Paying a repeated cost or a one-time cost without knowing how often the need recurs: spin or block (adaptive locks), scan or build an index, recompute or cache, interpret or compile (JIT tiers), reconnect or keep a connection | Ski rental: keep paying the repeated cost until it totals the one-time cost, then pay the one-time cost | The two costs are measured; changing the threshold changes timing, not results | Never more than twice the hindsight-optimal cost (deterministic); about 1.58 times with a randomized threshold |
| Choosing a cache eviction policy and judging how good it is | Compare against Belady's optimal policy (evict the item used furthest in the future), computed offline on a recorded access trace; LRU and FIFO are k-competitive for a cache of k items | A representative trace is available; Belady's policy is optimal only when every item has the same size and miss cost (with variable sizes, as in byte-capacity caches, the exact offline optimum is NP-hard, so compare against a published bound instead); see "Caching and eviction" in `techniques/data-structures.md` for the policies | Shows how much hit rate any policy could still gain on this workload |
| Jobs arriving one at a time must be assigned to identical machines | List scheduling: assign each job to the least-loaded machine (a heap of loads) | Jobs cannot be reassigned later; if all jobs are known first, sort them longest first ("Heuristics with guarantees") | Within 2 − 1/m of the optimal finishing time for m machines; O(log m) per job |
| Items arriving one at a time must be packed into bins | First fit (place in the first bin with room) | Approximate packing accepted; if all items are known first, use first-fit decreasing | At most 1.7 times the optimal number of bins |

## References

Sources: `references/techniques/optimization-and-scheduling.md`, read only to verify a claim.
