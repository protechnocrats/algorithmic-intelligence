# Behavior Traps

Rewrites that look equivalent but are not. Walk this list for every candidate in Phase 3 and again after applying a change. Each applicable trap must be covered by a differential test or ruled out with a stated reason. A trap that the change actually triggers is a behavior change: document it for developer review and do not apply it without explicit approval (rule 5). Language-specific traps are in the `languages/` files.

## Ordering

- **Iteration order of hash structures.** Replacing a list with a hash set or hash map, or an insertion-ordered map with an unordered one, changes the order callers see. Some platforms randomize hash order per process (Swift), so a test can pass once and fail later. Preserve order with an insertion-ordered structure, or keep the original list for output and use the hash structure only for lookups.
- **Sort stability.** Switching between a stable and an unstable sort changes the relative order of equal elements. Check which sorts are stable in the language file. Timsort and merge sort are stable; introsort, pattern-defeating quicksort, and heapsort are not.
- **Adaptive and hybrid algorithms.** When an implementation picks a branch by input size, shape, or CPU features, each branch can differ in stability, tie choice, `NaN` handling, floating-point bits, or errors. Tests at one size or on one machine then pass while other inputs differ. Test every branch, inputs on both sides of every crossover, and each CPU-feature variant.
- **Ties.** "First match," "max by," and "min by" may pick a different element among equals after a rewrite.
- **Enumeration order.** A faster enumeration (Gray-code, revolving-door, or swap-based permutation order; a different branching order in a search) visits the same items in a different order. That changes which solution is found first and the order of any output.
- **Shuffles and random selection.** Replacing a shuffle or a random choice changes the sequence produced for a given seed, and may change the distribution (a shuffle by random comparator is biased, Fisher-Yates is not). Both are behavior changes.
- **Order of side effects.** Batching, parallelizing, or reordering loops changes the order of writes, logs, events, and callbacks.

## Equality and keys

- **Equality semantics change.** A linear search with `==` or a custom comparison may not match the hash structure's equality (`equals`/`hashCode`, `Hashable`, `IEquatable`, JavaScript SameValueZero, reference equality for objects).
- **Inconsistent `equals` and `hashCode`.** Types that override one but not the other behave correctly in a list scan but break in a hash set.
- **Mutable keys.** An object used as a hash key and mutated afterward can no longer be found.
- **Case, culture, and normalization.** String comparisons that ignore case or depend on locale must use the same comparer in the new structure.
- **Floating-point keys.** `NaN`, `-0.0` versus `0.0`, and rounding make float keys unsafe in hash structures.

## Duplicates and nulls

- **Duplicates collapse.** Converting a list to a set removes duplicates; maps overwrite or throw on duplicate keys depending on the method used.
- **Null handling.** Some structures reject null keys or values; others accept them. A lookup that returned "not found" may now throw, or the reverse.

## Mutation and aliasing

- **Input mutation.** In-place algorithms (sorting the caller's list, removing during iteration) change the caller's data where the original did not, or the reverse.
- **Returned collections.** Returning an internal buffer, a view, or a mutable collection where the original returned a fresh copy lets callers mutate shared state.
- **Copy-on-write and value semantics.** Changes to when copies occur can change both performance and which copy a caller sees.
- **Aliased arguments.** An in-place algorithm that reads one argument while writing another breaks when both are the same object (for example, merging a list into itself, or copying into an overlapping buffer). An optimization that copies an argument the original modified in place, or that modifies in place what the original copied, changes what other references to that object see.
- **Object identity.** Returning the argument itself instead of a copy (or the reverse), returning a cached or shared instance, or interning values changes the results of identity checks (`===`, `is`, `ReferenceEquals`) and lets callers mutate state the original kept private.

## Laziness, short-circuiting, and evaluation

- **Eager versus lazy.** Switching between eager collections and lazy sequences or iterators changes when (and whether) element functions run, which matters when they have side effects, throw, or read changing state.
- **Short-circuiting lost.** A precomputed index built from all elements evaluates elements the original never touched, possibly throwing or doing extra I/O.
- **Deferred queries.** Lazy query objects (LINQ, ORM query builders) re-execute on every enumeration; caching or materializing them changes when the data is read.

## Numbers

For numerical code, matching outputs on ordinary inputs is not enough evidence. Test the edge values listed in `DIFFERENTIAL-TESTING.md` (NaN, infinities, signed zero, subnormals, extreme magnitudes).


- **Overflow.** A closed-form formula or a different summation order can overflow where the loop did not, or the reverse. Some languages wrap silently, others trap or crash.
- **Floating-point association.** `(a + b) + c` is not `a + (b + c)`. Prefix sums, reordering, and parallel reduction change results.
- **Integer division and rounding.** Rewritten arithmetic can round differently.
- **Bit manipulation width.** Shifts beyond the type width, signed versus unsigned shifts, and 32-bit limits in some runtimes.
- **Catastrophic cancellation.** Rewriting `a − b` forms (for example, expanding or factoring a formula) can lose most significant digits when the operands are close.
- **Overflow and underflow in intermediate values.** A rearranged formula can overflow to infinity or underflow to zero in an intermediate step even when the final result fits.
- **NaN, infinity, and signed zero.** NaN propagates differently through min/max, comparisons, and sorting; `-0.0` and `0.0` compare equal but differ in division and formatting. A rewrite must handle them exactly as the original did.
- **Exact versus tolerance comparisons.** Replacing exact equality with a tolerance (or the reverse) changes results.
- **Reproducibility.** Vectorized, fused multiply-add, and parallel computations can produce different bits from the sequential version, and different results across runs or machines.

## Machine learning

- **Random number consumption.** Reordering, batching, or parallelizing code that draws random numbers (initialization, dropout, shuffling, sampling) changes which number each draw receives, and therefore the results, even when the logic is equivalent. Compare with the same seed and the same draw order, or treat the difference as a behavior change.
- **Nondeterministic kernels.** Some GPU operations (atomic accumulation, some convolution and scatter algorithms) give different bits on every run. Differential tests need the framework's deterministic mode, or a tolerance the developer approves (`DIFFERENTIAL-TESTING.md`).
- **Batch-dependent numerics.** Batching, padding, or changing batch size can change results: batch normalization statistics, kernel selection by shape, and reduction order all depend on the batch.
- **Training versus inference mode.** Dropout and batch normalization behave differently in each mode. A rewrite that runs in the wrong mode, or switches mode, changes outputs.
- **Data types and promotion.** Lower precision, implicit type promotion, or a different accumulator type changes results, and can overflow (16-bit floats overflow above 65,504).
- **Tokenization.** Any change to tokenization (merge order, normalization, special tokens) changes model inputs and outputs, even when the text is the same.

## Images and signals

- **Border handling.** Filters treat pixels outside the image in different ways (clamp to edge, mirror, wrap, zero). A rewrite, a separable split, or an FFT must reproduce the original's choice at every border.
- **Rounding, clamping, and saturation.** 8-bit and 16-bit channels round and clamp at every stored step. Splitting a filter into passes, fusing passes, or using SIMD saturating arithmetic changes where rounding happens, and therefore the output.
- **Color space and gamma.** Averaging, blending, or resizing in gamma-encoded values gives different results from doing it in linear light. Keep the original's color space for each step.
- **Premultiplied alpha.** Converting between straight and premultiplied alpha, or filtering one as if it were the other, changes edges and transparent pixels.
- **Channel order and layout.** RGBA versus BGRA, planar versus interleaved, and row padding (stride) must be preserved where callers or files observe them.

## Geometry

- **Predicate robustness.** Orientation, in-circle, and point-in-polygon tests on nearly degenerate input can flip sign when the same formula is evaluated in a different order or precision. A flipped test changes topology: a different hull, a missing intersection, an invalid mesh.
- **Tolerances.** Changing an epsilon, where it is applied, or whether a comparison is strict changes which points merge, touch, or intersect.
- **Degenerate input.** Collinear and coincident points, zero-length edges, zero-area faces, and self-touching polygons are where rewrites most often differ. Test them explicitly.
- **Orientation and winding.** Output vertex order (clockwise or counterclockwise), face winding, and the starting vertex are observable to callers and renderers.

## Simulation and games

- **Determinism.** Lockstep multiplayer, replays, and saved simulations need identical results on every machine and every run. Reordering floating-point operations, parallelizing, or using fused multiply-add breaks determinism even when results look the same.
- **Update order.** The order in which objects update within a frame affects outcomes (which collision resolves first, which event fires first). Spatial structures and parallel updates change that order.
- **Time step.** Changing from variable to fixed time steps, or the step size, changes simulation results.
- **Frame timing of effects.** Moving work to another frame, a background thread, or an event changes when its effects appear, which players and other systems can observe.

## Strings and text

- **Length and indexing units.** UTF-16 code units, Unicode scalars, and grapheme clusters give different lengths and indices.
- **Locale-sensitive operations.** Case conversion and comparison that depend on the current locale.

## Removed work

Work that looks unnecessary often is not. Before avoiding or deleting any work, rule out each of these:

- **Unseen callers.** A result that no caller in the repository uses can still be used by callers outside it (a public library API, a service endpoint, a plugin interface), or through reflection, dependency injection, serialization, configuration, or templates. Public and exported code: treat every result as used.
- **Validation and errors.** A computation whose result is discarded may exist to throw on bad input (parsing to validate, a lookup that fails on a missing key). Removing it removes the error.
- **Side effects of reads.** In systems code, a read can have effects: device registers, memory-mapped I/O, `volatile` variables, page touches that fault memory in, and lazy initialization triggered by first access.
- **Timing and ordering on purpose.** Constant-time padding and dummy operations in security code, deliberate delays and backoff, memory fences, lock acquisitions that order other threads, and cache or JIT warm-up all look like wasted work. Removing them is a security or correctness regression.
- **"Nothing changed."** Skipping a refresh because inputs look unchanged is caching: every input must be known and every change detected (see "Caching traps").

## Purity and caching

### Hidden inputs

A function is not pure just because its arguments are unchanged. Before caching or memoizing, verify that the result does not depend on any of these:

- the current time, time zone, daylight-saving transitions, or calendar;
- locale, language, or culture settings;
- environment variables, feature flags, runtime configuration, or experiment assignments;
- the file system, network resources, or other external state;
- random number generators, random seeds, or nondeterministic iteration order;
- the current user, tenant, session, or permissions;
- process-specific state (process ID, memory addresses, hash seeds).

### Caching traps

- **Memoizing an impure function.** If the function depends on any hidden input above, or on mutable state or the database, a cache returns stale or wrong results.
- **Cache scope.** State whether a cache lives per call, per object, or process-wide. A wider scope than the original lifetime of the data causes staleness and leaks across users.
- **Cache invalidation.** A cache must be invalidated whenever any input it depends on changes.
- **Bounded caches evict.** Eviction changes which calls hit the slow path; that is fine only if the function is pure.

## Concurrency

- **Thread safety.** Replacing a synchronized or concurrent structure with an unsynchronized one, or adding shared mutable caches, introduces races.
- **Iterator invalidation.** Modifying a collection while iterating it throws or skips elements, depending on the platform.
- **Changed concurrency.** Running previously sequential work concurrently changes ordering, error behavior (fail-fast versus continue), rate limiting, and resource usage.
- **Optimistic and speculative execution.** A reader that proceeds without a lock (sequence locks, optimistic concurrency) can see torn or inconsistent data before it validates. It must not act on that data first: no pointer dereference, division, array index, or output. A retry repeats every side effect of the attempt, and speculative work done for a guess that turns out wrong must leave no trace (no writes, logs, or messages).
- **Missed changes.** Code that switches from rescanning to consuming changes (change feeds, file-system notifications, incremental maintenance) misses updates when the feed overflows, restarts, or is truncated. The original rescan never missed them. Every gap must be detected and fall back to a full rescan.

## Cancellation, timeouts, and resources

An optimization can return the same values in tests while changing production behavior:

- **Cancellation.** Batched or parallel work may ignore cancellation that the per-item loop honored, or cancel more work than before.
- **Timeouts.** One timeout around a batch behaves differently from a timeout per item; a slow item can now fail the whole batch.
- **Resource lifetimes.** File handles, database connections, streams, and locks may be held longer (or released earlier) when work is batched, cached, or made lazy.
- **Partial failure and cleanup.** Cleanup and rollback must still happen when only part of a batch succeeds.
- **Lock ordering.** Changing the order in which locks are taken, or holding a lock across more work, can introduce deadlocks and starvation.
- **Connection and thread pools.** More concurrency can exhaust pools that were sized for sequential use.

## Security-sensitive behavior

An optimization can be faster while making the system less secure. Treat every item below as a regression, never as a valid optimization:

- **Constant-time code.** Do not replace constant-time comparisons or computations (secrets, tokens, MACs, password hashes) with early-exit or data-dependent versions.
- **Authorization and validation.** Early exits, caching, batching, and reordering must not skip, reorder, or weaken authentication, authorization, or input validation checks.
- **Cache keys.** A cache key must include every input that affects the result, including user, tenant, permission, locale, and configuration context. Omitting one can leak data across users.
- **Adversarial inputs.** Hash-based structures can degrade to their worst case under hash flooding when attackers control keys; prefer structures with worst-case guarantees (or randomized hashing) for untrusted input.
- **Resource exhaustion.** A faster average case with a much worse worst case (unbounded caches, quadratic behavior on pathological input, unbounded recursion) can create a denial-of-service risk.

If an existing security weakness is found, it is a bug: document it and report it (rule 4). Techniques for optimizing safely under hostile input, around secrets, and under hard deadlines are in `techniques/hostile-inputs.md`.

## Errors and limits

- **Different exceptions.** A new structure may throw a different exception type, at a different point, or not at all.
- **Recursion depth.** Turning iteration into recursion (or the reverse) changes stack overflow behavior on large inputs. Removing an overflow on valid input is a bug fixed as a side effect (rule 4); introducing one is a regression and is never acceptable.
- **Resource limits.** A faster algorithm that uses more memory may hit OOM where the original did not (rule 1: memory must stay bounded).

## I/O and databases

- **Query count and transactions.** Batching queries changes transaction boundaries, locking, and what a concurrent writer can interleave.
- **Result order.** A database returns rows in no guaranteed order without `ORDER BY`; a batched `IN` query may order results differently from per-item queries.
- **Partial failure.** One failed item in a batch may fail the whole batch where the loop processed the others.

## Public contract

- **Signature, return type, nullability, mutability, and threading guarantees** must stay the same unless the developer approves the change (rule 11).

## References (for verifying claims; not required reading)

- David Goldberg, "What Every Computer Scientist Should Know About Floating-Point Arithmetic," *ACM Computing Surveys* 23(1), 1991.
- Scott A. Crosby and Dan S. Wallach, "Denial of Service via Algorithmic Complexity Attacks," USENIX Security 2003.
