# Hardware, Parallelism, and Concurrency

The shared rules and table conventions in `ADVANCED-TECHNIQUES.md` apply to every table here.

## Memory locality

Select these when a profile, cache-miss or branch-miss counters, or a benchmark shows memory access or the pipeline is the bottleneck. Apart from sparse representations, complexity does not change; constant factors can change several-fold.

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Hot loops read one field from many objects (pointer chasing, scattered allocations) | Data-oriented layout: structure of arrays (SoA) instead of array of structures (AoS); flat primitive arrays | Callers do not depend on object identity or the object API, or an adapter keeps it | Fewer cache misses; vectorization becomes possible |
| Linked structures traversed in hot paths | Contiguous arrays, index-based links, arena or pool allocation | Nothing holds a pointer or reference across a growth or compaction that moves elements; node identity is not observable; an arena is freed as a whole, so its lifetime matches the longest-lived element | Sequential access instead of pointer chasing |
| Nested loops over large 2D data (matrix multiply, image filters, grid passes) | Loop interchange to match memory order; loop tiling/blocking | Reordering does not change results (floating-point summation order does) | Working set fits in cache |
| Several passes over the same large arrays, each limited by memory bandwidth; or one loop doing unrelated work that blocks vectorization | Loop fusion (merge passes so data is read once while in cache) or loop fission (split a loop so each part vectorizes or fits in cache) | No pass depends on results a later element of another pass produces; floating-point evaluation order unchanged | Same complexity; fewer trips through memory, or vectorized inner loops |
| Threads updating counters or fields that share a cache line | Padding or per-thread accumulators combined at the end (avoid false sharing) | Combining preserves the original result | Removes cache-line contention |
| Many short-lived allocations in hot code | Allocation reduction: reuse buffers, preallocate, pooling | Reused objects are never retained by callers or other threads, and are fully cleared before reuse, or one request's data or secrets leak into the next | Less GC and allocator time |
| Throughput limited by bytes moved, not computation | Compact representations (smaller integer types, bit packing, compression of cold data) | Value ranges are proven to fit for every value callers can pass, not only the test data: a narrower type wraps or truncates silently in many languages | Less memory bandwidth |
| Data that is mostly zeros or one repeated value | Sparse representation (sorted index-value pairs, hash map of non-default entries, CSR) instead of dense, or the reverse when density is high | Density measured on real data; the default value is reported the same way | Memory and time proportional to non-default entries; dense wins above a measured density |
| Binary search over a large static sorted array | Eytzinger (breadth-first) layout with prefetching, or a static B-tree layout | Data unchanged between searches; results identical, including which duplicate is returned | Same O(log n); far fewer cache misses |
| Divide-and-conquer over large data on hardware with unknown or several cache levels | Cache-oblivious algorithms and layouts: recursive matrix transpose and multiply, van Emde Boas layout for static trees, funnel sort | Results identical (floating-point summation order changes them) | Near-optimal cache misses at every level without tuning to a cache size |
| Code tuned to one cache size (tile size, block size) | Cache-aware blocking with the size measured or queried on the target | Target hardware is known | Better constants than cache-oblivious on that hardware; worse on others |
| Unpredictable branches in a hot loop (comparisons on random data, filters) | Branchless code: conditional moves, masks, arithmetic selection | Profile shows branch mispredictions; results identical | Constant factor; often slower when the branch is predictable, so measure on real data |
| Choice between an asymptotically better and a simpler structure at small sizes (linear scan versus hash lookup, insertion sort versus merge sort) | Measured crossover threshold, with the simple method below it | Threshold measured on the target hardware and data; both paths give identical results | Faster at small n without losing the asymptotic bound at large n |
| Many independent lookups into a structure much larger than cache (hash probes in a join, tree descents, graph frontier expansion), each stalling on a miss | Software prefetching with interleaved lookups: compute the addresses for a batch of keys, issue prefetches, then finish each lookup (group prefetching, as in database hash joins), or coroutine-interleaved lookups | Lookups are independent; the batch size is measured (too large evicts its own prefetches); results and their order identical | Memory latency overlapped across the batch; same asymptotic cost, often several times faster |

## What the compiler already does

Statement-level rewrites by hand (inlining, common-subexpression elimination, hoisting invariants, constant folding, strength reduction, unrolling, bounds-check removal, keeping non-escaping objects off the heap) mostly duplicate what optimizing compilers and JITs already do when they can prove it safe, and can block the compiler's own transformation. Compilers cannot be relied on to change an algorithm's complexity, so this check applies only to such rewrites.

- **Look before rewriting.** Read the generated code (Compiler Explorer, `objdump`, `-S` output, JIT disassembly such as `-XX:+PrintAssembly` or .NET's disassembly diagnostics) or the optimizer's reports (`-Rpass` and `-Rpass-missed` in Clang, `-fopt-info` in GCC). Missed-optimization reports name the reason, such as possible aliasing, a call the compiler cannot see through, or floating-point strictness.
- **Help the compiler instead of replacing it.** Make aliasing explicit (`restrict` in C, separate slices in Rust), keep hot loops free of opaque calls, move rare paths out of line, and use link-time or profile-guided optimization when the build allows (a build change, so ask). Floating-point reassociation flags such as `-ffast-math` change results.

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Generic or configurable code where the configuration is fixed at the call site or at startup (interpreters, query engines, serializers, regex and filter evaluators, dynamic dispatch on a type known at the call site) | Specialization and partial evaluation: generate or select code for the known values (monomorphization, templates or generics specialized per type, compiling a query or filter expression to a closure or to code once, JIT specialization) | Every specialized version passes the same differential tests as the generic one; the number of specializations, and any cache of compiled versions keyed by input, is bounded (code size and compile time); expressions from untrusted input go through a generator that cannot emit arbitrary code, never through building source text and evaluating it | Interpretive overhead per element removed: often several times faster on the hot path |
| A tree-walking interpreter or a filter expression evaluated per row or per packet | Compile once to bytecode, closures, or native code (as with BPF programs, query compilation in databases, and regex compilation) | Same results, errors, and evaluation order as the interpreter, including short-circuiting | Per-node dispatch and allocation removed |

## Parallelism and vectorization

Parallelism reduces wall-clock time, not total work, and adds overhead. Use it only after the sequential algorithm is optimal.

- **Amdahl's law.** With a fraction p of the work parallel on N cores, the best speedup is 1 / ((1 − p) + p / N). Estimate p from a profile before proposing parallelism.
- **Work and span.** On P cores the time is at least max(T₁ / P, T∞) for work T₁ and span T∞ (the longest chain of operations that must run in order); a greedy scheduler gets within a factor of two of that bound. Parallelism T₁ / T∞ should be about ten times P or more to keep P cores busy. A loop whose steps each depend on the previous one has span O(n) at any core count: restructure the dependency first (move 9 in `DISCOVERY.md`).
- **Overhead.** Scheduling, thread creation, synchronization, and data transfer make small inputs slower: find the size below which sequential execution wins.
- **Load imbalance.** Uneven chunks leave cores idle; use work stealing or smaller chunks.
- **Determinism.** Parallel floating-point reductions change summation order and therefore results; with checked or saturating integer arithmetic, an overflow can appear or vanish when the order changes; the order of side effects, logging, and errors also changes.
- **Hidden shared state.** Check everything the parallel work calls, not only the loop body: a collection appended to, a counter, a cache or lazily initialized field, a random generator, or a library object that is not thread-safe (some date formatters, parsers, and database connections). Each is a race until synchronized or made per thread.
- **Bounded threads.** Parallelism inside a request multiplies by the number of concurrent requests, and nested parallel loops multiply each other: size pools for the total.

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Independent per-element work over large arrays | SIMD/vectorized operations: compiler auto-vectorization, platform vector APIs, vectorized libraries | Simple loops without data-dependent branches; results identical (floating-point reassociation changes them) | Several times faster per core |
| Large independent tasks or data partitions | Task or data parallelism with a bounded thread pool | Tasks are truly independent; shared state is synchronized or eliminated | Up to the Amdahl limit |
| Associative reductions over large data | Parallel reduction with per-thread partial results | The operation is associative; floating-point results differ unless the reduction order is fixed | Up to the Amdahl limit |
| Running totals or other prefix computations over large arrays on many cores | Parallel prefix scan (work O(n), span O(log n)) | The operation is associative; floating-point results differ from the sequential order | Up to the parallelism available, where a sequential loop has span O(n) |
| Pipelines of independent stages | Pipelining with bounded queues | Stage order and backpressure preserve semantics | Overlaps I/O and compute |
| One build must run on CPUs with different instruction sets, so hot routines use only the baseline set | Runtime dispatch by CPU feature: select an implementation once at startup or load time (GNU `ifunc`, function multiversioning, a function pointer set after feature detection, the kernel's alternatives patching) | Every variant passes the same differential tests, including the scalar fallback; floating-point variants give identical bits or the difference is reported; selection happens once, not per call | Vector speedups where the hardware has them, with no loss on older CPUs |

### Contention and synchronization

Threads waiting on the same lock, atomic, or cache line can cost more than the work itself, and adding cores makes it worse. Select these when a profile shows lock wait time, contended atomics, or cache-line transfers. Differential tests cannot cover thread interleavings: unless a stress test, a race detector (ThreadSanitizer or the platform's equivalent), or a model checker covers the change, it is unverified and needs the developer's approval with a `NEEDS-TESTING` marker.

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Many threads update one shared counter or statistic | Per-thread or per-CPU counters summed when read (striped counters, such as Java's `LongAdder`) | No reader needs an exact instantaneous value: the sum is not an atomic snapshot | Updates no longer contend; a read costs O(threads) |
| One lock guards a large map or table, and profiles show contention on it | Lock striping: split into shards selected by key hash, one lock per shard | Each operation touches one shard, or multi-shard operations take shard locks in one fixed order | Contention divided by about the shard count |
| Data read far more often than written, with readers serialized by a lock | Reader-writer lock; or read-copy-update (RCU) or copy-on-write snapshots, where writers publish a new version and readers take no lock | Readers tolerate seeing the previous version until their read finishes; old versions are freed only after every reader that may hold them has finished | Reads proceed in parallel without lock acquisition; writes pay a copy |
| Lock held during slow work (I/O, allocation, logging, callbacks) | Shrink the critical section: prepare outside the lock, hold it only to publish | Every invariant the lock protects still holds whenever another thread can observe the data | Less waiting; same total work |
| Small shared data read very often, written rarely, and readers must never block the writer (timekeeping, statistics, configuration snapshots) | Sequence lock: the writer increments a counter before and after writing; a reader copies the data and retries if the counter was odd or changed | Readers act on their copy only after validation, never on a possibly torn value (no pointer dereference, division, or array index from unvalidated data); writers are serialized among themselves; reader retries under frequent writes are acceptable | Readers take no lock and write no shared cache line |
| Updates that conflict rarely, but every one takes a lock (read-modify-write of records, version counters, transactions) | Optimistic concurrency: read a version, compute, then commit with a compare-and-swap or a version check, retrying on conflict | The operation can be retried without repeating external side effects; the measured conflict rate is low; retries are bounded or backed off so they cannot livelock | No lock held during the computation; the cost moves to retries, which grow with contention |
| Critical sections much shorter than a sleep and wake-up, with threads blocking on them often | Adaptive lock: spin briefly while the holder is running on another CPU, then block (adaptive mutexes, futex-based locks) | More than one CPU; the holder is not preempted while spinning; real-time or priority-inheritance requirements still met | Fewer context switches; spinning wastes CPU when critical sections are long, so measure |
| Single producer and single consumer exchanging items through a locked queue | Lock-free bounded ring buffer with acquire and release memory ordering | Exactly one producer thread and one consumer thread; memory ordering correct on every target architecture; behavior when full (block, drop, or fail) matches the original | No lock per item |

General lock-free and wait-free structures (multi-producer queues, lock-free hash maps) are easy to get wrong: prefer the platform's own concurrent structures, or a reviewed library (rule 7).

## References

Sources for the claims in this file are in `references/techniques/hardware-and-concurrency.md`. Read them only to verify a claim.
