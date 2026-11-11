# Games and Real-Time Simulation

The shared rules and table conventions in `ADVANCED-TECHNIQUES.md` apply to every table here.

## Games and real-time simulation

A frame has a fixed budget (16.7 ms at 60 frames per second), so the worst frame matters more than the average: measure frame-time percentiles and spikes, not only means. Spatial queries and broad-phase collision are in `techniques/spatial-data.md`; ray casts and visibility use the BVH under "Computational geometry and CAD" in `techniques/geometry-and-cad.md`. Levels, saves, replays, and mods made by players are untrusted input: keep size limits on what they declare, and do not load them with formats that run code.

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Many agents each finding a path to the same goal | Flow field: one Dijkstra or BFS outward from the goal, then each agent follows the cheapest neighbor | Agents share the goal and the cost map; costs are non-negative (Dijkstra); among equal-cost paths, agents may pick different ones | One A* search per agent per update → one search per goal change, then O(1) per agent per step |
| Pathfinding on a large uniform-cost grid | Jump point search | Uniform costs and the original movement rules (diagonals, corner cutting); optimal length, but may choose a different path among equals | Same optimal length with far fewer nodes expanded |
| Pathfinding over large maps, repeated often | Hierarchical pathfinding (HPA*), navigation meshes, or precomputed portal graphs | HPA* and navigation-mesh or portal paths can be longer than the optimal grid path (a behavior change) | Large practical reduction in search work |
| Every object's world transform recomputed every frame | Dirty flags on the transform hierarchy: recompute only the subtrees that changed | Every change marks its node | O(all nodes) → O(changed nodes) per frame |
| Every object updated or polled every frame although few change | Event-driven updates, timers (timing wheel), sleeping physics bodies | Update order and the timing of effects are preserved, or the change is approved | Work proportional to active objects |
| Every object drawn or tested for visibility each frame | Frustum culling over a BVH or grid; occlusion culling | Culling is conservative: it never removes a visible object | O(objects) → about O(log n + visible objects) |
| Distant objects rendered or simulated at full detail | Level of detail (LOD) for meshes, animation, and simulation | Changes what is rendered or simulated (a behavior change) | Work roughly proportional to screen-space importance |
| Narrow-phase collision between convex shapes by testing all pairs of features | GJK, with EPA for penetration depth; the separating axis theorem for boxes and simple polyhedra | GJK and EPA are iterative with tolerances, so contact points and depths can differ from the original: compare them. In 3D the separating axis theorem tests every face normal and every pair of edges, so it is not linear for complex hulls | Feature pairs O(n·m) → about O(n + m) per query with GJK |
| Allocation, garbage collection, or asset loading during gameplay | Object pools, preallocated buffers, asynchronous asset streaming | Pooled objects are fully reset before reuse | Removes frame-time spikes |
| Game objects with their data scattered across memory | Entity-component-system storage: each component type in a contiguous array | See "Memory locality" in `techniques/hardware-and-concurrency.md` | Fewer cache misses per frame |
| Assets, events, or properties looked up by string name during frames | Hash names to integer IDs once at load time | IDs are unique; collisions detected at load time | String hashing and comparison removed from frames |

## Game-tree search

For game AI, puzzle solvers, and any adversarial or turn-based search. The returned move and score are both observable, so a faster search must return the same move and score.

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Full minimax over a game tree of branching factor b and depth d | Alpha-beta pruning | Returns the same root value as minimax; the same move only if ties among equal-valued moves are broken the same way (alpha-beta may stop at the first best move it finds) | O(b^d) → about O(b^(d/2)) with good move ordering; O(b^d) with the worst ordering |
| Alpha-beta that searches poor moves first | Move ordering: the best move from the previous iteration first, then captures, killer moves, and the history heuristic | Ordering changes only pruning, never the value; tie-breaking among equal moves checked as above | Closer to the O(b^(d/2)) best case |
| The same position reached by different move orders and searched again | Transposition table keyed by a Zobrist hash (XOR of a random number per piece and square, updated incrementally), with a fixed size and a replacement policy | Hash collisions verified or made negligible with 64-bit keys; stored bounds (exact, lower, upper) used correctly with the alpha-beta window; table size bounded. Reusing an entry from a deeper search, or for a position whose value depends on how it was reached (repetition rules), returns a different score than the fixed-depth search: require an exact depth match and path-independent evaluation | Repeated subtrees searched once; position hashing O(1) per move instead of O(board) |
| A fixed-depth search that must finish within a time budget | Iterative deepening: search depth 1, 2, 3, … until time runs out, reusing the previous iteration's best move for ordering | Depth reached now depends on time and machine speed, unlike a fixed-depth original | Uses the budget fully; the overhead of shallower iterations is small, since the last depth dominates |
| Branching factor too large for alpha-beta (Go, large strategy games), or no reliable evaluation function | Monte Carlo tree search with UCT selection | Results are randomized and approximate, unless it replaces another randomized search with the same seeding; the tree grows every iteration, so cap its node count as well as the time | Effort concentrated on promising moves; anytime: quality improves with time |

## Behavior traps

Rewrites that look equivalent but are not; check them alongside `BEHAVIOR-TRAPS.md`.

- **Determinism.** Lockstep multiplayer, replays, and saved simulations need identical results on every machine and every run. Reordering floating-point operations, parallelizing, using fused multiply-add, or calling a different math library's `sin` or `sqrt` approximation breaks determinism even when results look the same.
- **Update order.** Object update order within a frame affects outcomes (which collision resolves first, which event fires first). Spatial structures and parallel updates change that order.
- **Time step.** Changing from variable to fixed time steps, or the step size, changes simulation results. Measure frame time with a monotonic clock: wall-clock time jumps when the system clock is corrected or changed, giving negative or huge steps.
- **Frame timing of effects.** Moving work to another frame, a background thread, or an event changes when its effects appear, which players and other systems can observe.
