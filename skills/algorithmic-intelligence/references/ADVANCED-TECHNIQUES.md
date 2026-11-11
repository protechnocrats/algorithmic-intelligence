# Advanced Techniques

An index of the domain files under `techniques/`, for when the core techniques do not reach the lower bound or the problem belongs to a specialized domain. A problem can span several (a game's collision detection needs both `techniques/spatial-data.md` and `techniques/games-and-simulation.md`). Match on the abstract problem, not on the code's surface.

## Domain files

| File | Open when the problem involves |
|---|---|
| `techniques/graphs-and-trees.md` | Graphs, static or changing (adjacency list, matrix, or compressed representation; shortest paths, connectivity, ordering, matching, flows, incremental recomputation over dependency graphs, dynamic trees), compiler analyses (dataflow, SSA, dominators, register allocation), and tree queries |
| `techniques/sequences-dp-search.md` | Range queries over arrays, dynamic programming that is still too slow, exponential search (subsets, constraints, puzzles, exact cover), enumeration orders and shuffling, and what to do once a problem is NP-hard (parameters, approximation, heuristics) |
| `techniques/strings-and-text.md` | Substring and pattern search, palindromes, edit distance, regular expressions, keyword search and top-k ranked retrieval, string sorting and tries, expression parsing, diffs, text buffers, line breaking, and automata: lexers, state-machine protocol parsers, grammar parsers |
| `techniques/math-and-numerics.md` | Primes, divisibility, modular arithmetic, recurrences, convolution, floating-point summation and accuracy, polynomials, linear systems, sparse matrices, matrix multiplication, quadrature, numerical optimization, and quantum simulators and circuit compilers |
| `techniques/machine-learning.md` | Data pipelines for models, training, inference, LLM serving and decoding, embeddings and retrieval, classical machine learning, and calls to model APIs |
| `techniques/images-and-signals.md` | Filters, convolution, blurs, morphology, per-pixel operations, color transforms, labeling, multi-scale images, video frames, and audio |
| `techniques/geometry-and-cad.md` | Convex hulls, segment intersection, point-in-polygon, ray casting, triangulation, meshes, polygon Booleans, curves, and geometric predicates |
| `techniques/games-and-simulation.md` | Per-frame work, pathfinding for many agents, transform hierarchies, culling, level of detail, narrow-phase collision, frame-time spikes, and game-tree search (alpha-beta, transposition tables, iterative deepening, Monte Carlo tree search) |
| `techniques/spatial-data.md` | Proximity, collision, range, and nearest-neighbor queries over points or shapes in 2D, 3D, or high dimensions (including embeddings) |
| `techniques/hardware-and-concurrency.md` | Cache misses, branch misses, data layout, prefetching, what the compiler already optimizes, specialization and partial evaluation, SIMD and CPU-feature dispatch, multithreading, parallel reductions, lock contention, and optimistic concurrency (sequence locks, compare-and-swap retry, adaptive locks) |
| `techniques/data-at-scale.md` | Data larger than memory, fixed memory budgets, streaming aggregation, on-disk indexes, storage engines, file systems, data skipping, readahead, change propagation (materialized views, change feeds, log shipping), and compression and encoding |
| `techniques/specialized-structures.md` | Custom hash tables (multiplicative, cuckoo, d-left), making static structures dynamic, cache eviction policies, Bloom (double hashing, counting) and cuckoo filters, sketches, timing wheels, interval trees, integer-universe structures, splay trees and decrease-key heaps, persistent structures, decision diagrams, and longest-prefix match and packet classification |
| `techniques/optimization-and-scheduling.md` | The best assignment, schedule, route, packing, or allocation: polynomial special cases (assignment, flows, greedy schedules, matroids), linear, integer, and constraint programming, approximation heuristics, several objectives, and online decisions (rent or buy, eviction, online scheduling and packing) |
| `techniques/hostile-inputs.md` | Untrusted input, secrets, or hard deadlines: algorithmic complexity attacks, constant-time code and timing side channels, worst-case execution time, finding worst-case inputs. Opened by the exposure check (`WORKFLOW.md`, Phase 2) whether or not the core techniques suffice |
| `techniques/distributed-systems.md` | Work spread across machines: key placement and resharding, partitioning and skew, shuffles and distributed sorting, CRDTs, consensus throughput and reads, distributed transactions and locks, gossip, quorums |
| `techniques/queues-and-latency.md` | Waiting time rather than work: queues, pools, schedulers, backpressure, head-of-line blocking, tail latency and fan-out, batching, hedged requests, retries, adaptive rate limits. Opened when the resource check (`WORKFLOW.md`, Phase 2) finds time spent waiting |

## How to read the tables

The domain files use the columns of `CORE-TECHNIQUES.md` and read the same way (see the notes at the top of its "Signals and techniques").

## Shared rules

What holds across the domain files:

- **The preconditions are strict.** Confirm each from what the code enforces. With untrusted input, judge randomized, hashed, adaptive, and search-based techniques by their worst case (`techniques/hostile-inputs.md`).
- **Standard libraries rarely include them,** so follow "When the best technique is not available" in `ALGORITHM-ARSENAL.md`: a direct dependency first, then a maintained package offered beside writing it. A structure written in the project is short, with its own tests ("Testing a new data structure" in `DIFFERENTIAL-TESTING.md`) and a comment naming the technique and its complexity; a large or subtle one waits for the developer's decision (rule 7).
- **Exact answers with random running time are not behavior changes; approximate answers are.** A Bloom or cuckoo filter followed by the exact check, a hash match confirmed by direct comparison, and randomized quickselect for a single order statistic all stay exact: label their bounds expected, and draw the randomness from a source an attacker cannot predict or observe. Top-k or a partition by quickselect is different: which of several equal elements at the boundary gets selected depends on the pivots, so it is a behavior change unless ties are broken deterministically. Sketches, sampling, approximate nearest neighbor, and probabilistic primality tests without a deterministic base set change answers (rule 5).
- **Parallel versions change behavior unless shown otherwise**: output and side-effect order, regrouped floating-point sums, races, run-to-run determinism. Keep the worker count bounded. See "Concurrency" in `BEHAVIOR-TRAPS.md` and "Parallelism and vectorization" in `techniques/hardware-and-concurrency.md`.
- **Several win only at large sizes,** so benchmark at realistic sizes.
- **A behavior change is a decision, not a disqualification.** When the best technique changes results (more accurate floating-point sums, a different eviction order, approximate answers), report it with the exact before and after and the best equivalent alternative beside it, and let the developer choose.
