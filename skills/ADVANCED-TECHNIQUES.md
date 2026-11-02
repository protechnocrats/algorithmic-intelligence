# Advanced Techniques

Load this file in Phase 3 alongside `ALGORITHM-ARSENAL.md` (or in write mode, step 4) when the core techniques do not reach the lower bound, or when the problem falls in one of the domains below. Then load only the domain files whose topics match. Load several when a problem spans domains (for example, a game's collision detection needs `techniques/spatial-data.md` and `techniques/games-and-simulation.md`). If no row matches but the core techniques fall short, scan the "Load when the problem involves" column again for the abstract problem from Phase 3, not the code's surface.

## Domain files

| File | Load when the problem involves |
|---|---|
| `techniques/graphs-and-trees.md` | Graphs, static or changing (shortest paths, connectivity, ordering, matching, flows, incremental recomputation over dependency graphs, dynamic trees), compiler analyses (dataflow, SSA, dominators, register allocation), and tree queries |
| `techniques/sequences-dp-search.md` | Range queries over arrays, dynamic programming that is still too slow, exponential search (subsets, constraints, puzzles, exact cover), enumeration orders and shuffling, and what to do once a problem is NP-hard (parameters, approximation, heuristics) |
| `techniques/strings-and-text.md` | Substring and pattern search, palindromes, edit distance, regular expressions, keyword search and top-k ranked retrieval across documents, string sorting and tries, expression parsing, diffs, text buffers, line breaking, and automata: lexers, state-machine protocol parsers, and grammar parsers |
| `techniques/math-and-numerics.md` | Primes, divisibility, modular arithmetic, recurrences, convolution, floating-point summation and accuracy, polynomials, linear systems, sparse matrices, matrix multiplication, quadrature, numerical optimization, and quantum simulators and circuit compilers |
| `techniques/machine-learning.md` | Data pipelines for models, training, inference, LLM serving and decoding, embeddings and retrieval, classical machine learning, and calls to model APIs |
| `techniques/images-and-signals.md` | Filters, convolution, blurs, morphology, per-pixel operations, color transforms, labeling, multi-scale images, video frames, and audio |
| `techniques/geometry-and-cad.md` | Convex hulls, segment intersection, point-in-polygon, ray casting, triangulation, meshes, polygon Booleans, curves, and geometric predicates |
| `techniques/games-and-simulation.md` | Per-frame work, pathfinding for many agents, transform hierarchies, culling, level of detail, narrow-phase collision, frame-time spikes, and game-tree search (alpha-beta, transposition tables, iterative deepening, Monte Carlo tree search) |
| `techniques/spatial-data.md` | Proximity, collision, range, and nearest-neighbor queries over points or shapes in 2D, 3D, or high dimensions (including embeddings) |
| `techniques/hardware-and-concurrency.md` | Cache misses, branch misses, data layout, prefetching, what the compiler already optimizes, specialization and partial evaluation, SIMD and CPU-feature dispatch, multithreading, parallel reductions, lock contention, and optimistic concurrency (sequence locks, compare-and-swap retry, adaptive locks) |
| `techniques/data-at-scale.md` | Data larger than memory, fixed memory budgets, streaming aggregation, on-disk indexes, storage engines, file systems, data skipping, readahead, change propagation (materialized views, change feeds, log shipping), and compression and encoding |
| `techniques/data-structures.md` | Custom hash tables (including multiplicative, cuckoo, and d-left hashing), making static structures dynamic, cache eviction policies, Bloom (including double hashing and counting variants) and cuckoo filters, sketches, timing wheels, interval trees, integer-universe structures, splay trees and decrease-key heaps, persistent (immutable) structures, decision diagrams, and longest-prefix match and packet classification |
| `techniques/optimization-and-scheduling.md` | Searching for the best assignment, schedule, route, packing, or allocation: polynomial special cases (assignment, flows, greedy schedules, matroids), linear, integer, and constraint programming, approximation heuristics, several objectives, and online decisions (rent or buy, eviction, online scheduling and packing) |
| `techniques/hostile-inputs.md` | Untrusted input, secrets, or hard deadlines: algorithmic complexity attacks, constant-time code and timing side channels, worst-case execution time, and finding worst-case inputs |
| `techniques/distributed-systems.md` | Work spread across machines: key placement and resharding, partitioning and skew, shuffles and distributed sorting, CRDTs, consensus throughput and reads, distributed transactions and locks, gossip, and quorums |
| `techniques/queues-and-latency.md` | Waiting time rather than work: queues, pools, schedulers, backpressure, head-of-line blocking, tail latency and fan-out, batching, hedged requests, retries, and adaptive rate limits |

## How to read the tables

Every domain file uses the same columns. Read them the same way as in `CORE-TECHNIQUES.md`: build or preprocessing cost is stated separately from per-query cost, output cost counts, bounds are worst case unless labeled expected, average, or amortized, and "in practice" marks workload-dependent speedups.

## Shared rules

These techniques apply to any codebase: operating system kernels, storage and database engines, file systems, compilers, search engines, machine learning and AI systems, image, video, and audio processing, CAD and geometry kernels, scientific and financial code, games and simulations, infrastructure tooling, backends, and apps. Every rule still applies. In particular:

- **Assumptions decide validity.** Each technique below has strict preconditions. Confirm each one from the code and record the evidence.
- **Most need an implementation inside the project.** Standard libraries rarely include them. Write a focused implementation with its own tests (see "Testing a new data structure" in `DIFFERENTIAL-TESTING.md`) and a comment naming the technique and its complexity (rule 13). If a well-tested library is the better route, ask first (rule 7).
- **Approximate results are always behavior changes.** Any technique whose answer can differ from the exact answer callers receive today (sketches, sampling, approximate nearest neighbor, probabilistic primality tests without a deterministic base set) needs developer review (rule 5). Randomized or probabilistic techniques whose final answer stays exact are not behavior changes on that account: a Bloom or cuckoo filter followed by the exact check, a hash match confirmed by direct comparison, randomized quickselect. Their randomness affects only running time; label those bounds as expected.
- **Constant factors matter.** Several techniques win only at large sizes. Benchmark at realistic sizes (rule 8).
- **A behavior change is a decision, not a disqualification.** When the best technique changes results (more accurate floating-point sums, a different eviction order, approximate answers), still report it with the exact behavior before and after, and let the developer decide (rule 5). Offer the best equivalent alternative next to it.
