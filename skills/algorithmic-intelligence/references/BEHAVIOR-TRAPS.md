# Behavior Traps

Rewrites that look equivalent but are not. Walk this list for each candidate and again after applying a change.
- **Cover or rule out each trap.** Each trap that could apply is either covered by a differential test or ruled out by a reason taken from the code and the inputs callers can pass. A "cannot happen" in a comment or test name is a claim ("Untrusted content" in `SKILL.md`).
- **A trap the change triggers is a behavior change** (rule 5) when the difference reaches the outcome. It stays one until you show every caller absorbs it ("Rule 11" in "Rule details" in `WORKFLOW.md`). When you cannot tell, explain and ask.
- **Other traps.** Language-specific traps are in the `languages/` files. Machine learning, images and signals, geometry, and games and simulation each have a "Behavior traps" section in their `techniques/` file, worth walking even when no technique from it is used.

**Contents:** Ordering · Equality and keys · Duplicates and nulls · Mutation and aliasing · Laziness, short-circuiting, and evaluation · Numbers · Strings and text · Time and dates · Removed work · Purity and caching · Concurrency · Cancellation, timeouts, and resources · Security-sensitive behavior · Errors and limits · I/O and databases

## Ordering

- **Hash iteration order.** Replacing a list or an insertion-ordered map with a hash structure changes the order callers see. Some platforms randomize it per process (Swift, Python strings, Java `Map.of`) or per map (Rust), so a test can pass once and fail later. Use an insertion-ordered structure, or keep the list for output and use the hash only for lookups.
- **Sort stability.** Timsort and merge sort are stable; introsort, pattern-defeating quicksort, and heapsort are not. Switching changes the order of equal elements. The language file says which built-in sorts are which.
- **Adaptive and hybrid algorithms.** An implementation that picks a branch by input size, shape, or CPU features can differ per branch in stability, tie choice, NaN handling, float bits, or errors, so tests at one size on one machine pass while other inputs differ. Test both sides of every crossover and each CPU-feature variant.
- **Ties.** "First match", "max by", and "min by" can pick a different element among equals, and so can replacing a sort followed by first or last with a minimum or maximum. Reversing a sorted result reverses equal elements; a descending comparator does not.
- **Upstream order.** Code that stops sorting, or merges instead, relies on order established somewhere else. A database `ORDER BY` can use a different collation or break ties differently from the in-memory comparator, and a later change upstream silently breaks the assumption unless a test pins it ("Pin what the change assumes" in `DIFFERENTIAL-TESTING.md`).
- **Comparator contract.** A comparator that is not a consistent total order (NaN, mixed types, inconsistent ties, state read during the sort) gives algorithm-dependent output, an exception (Java's TimSort), or memory corruption (some `qsort` implementations). Changing the sort exposes it.
- **Enumeration order.** A faster enumeration (Gray-code or swap-based permutation order, a different branching order in search) visits the same items in another order, changing which solution is found first.
- **Shuffles and random selection.** A different shuffle or choice changes the sequence for a given seed and may change the distribution (shuffling with a random comparator is biased; Fisher-Yates is not).
- **Order of side effects.** Batching, parallelizing, or reordering loops reorders writes, logs, events, and callbacks.

## Equality and keys

- **Different equality.** A linear search with `==` or a custom comparison may not match the hash structure's equality (`equals`/`hashCode`, `Hashable`, JavaScript SameValueZero, reference equality for objects). A type that overrides `equals` but not `hashCode` works in a list scan and breaks in a hash set.
- **Mutable keys.** A key mutated after insertion can no longer be found.
- **Floating-point keys.** NaN never equals itself, `-0.0` and `0.0` may hash apart, and rounding splits values that were meant to match.
- **Numeric identity.** `1` and `1.0`, or decimals `2.50` and `2.5`, can be equal under one comparison and distinct under the one a hash structure uses. Ruby's `==` matches them but hash keys use `eql?`, which does not. In Java, `equals` (used by `HashMap`, `HashSet`, `List.contains`) treats `Integer` 1 and `Long` 1 as different and compares `BigDecimal` scale, so a `TreeSet` and a `HashSet` disagree. Python is the reverse: `1`, `1.0`, and `True` are one key.

## Duplicates and nulls

- **Duplicates collapse.** A set drops them; a map overwrites or throws depending on the method.
- **Which duplicate wins.** A linear search returned the first match, while most ways of building an index keep the last or throw. Build the index so the first stays, or show that keys are unique.
- **Nulls.** Some structures reject null keys or values; a lookup that returned "not found" may now throw, or the reverse.

## Mutation and aliasing

- **Input mutation.** In-place algorithms change the caller's data where the original did not, or the reverse.
- **Returned collections and identity.** Returning an internal buffer, a view, a cached or interned instance, or the argument itself where the original returned a fresh copy (or the reverse) changes identity checks (`===`, `is`, `ReferenceEquals`) and lets callers mutate shared state. Copy-on-write changes which copy a caller sees.
- **Aliased arguments.** An in-place algorithm that reads one argument while writing another breaks when both are the same object (merging a list into itself, copying into an overlapping buffer). Copying what the original modified in place, or modifying what it copied, changes what other references see.

## Laziness, short-circuiting, and evaluation

- **Eager versus lazy.** Switching between collections and lazy sequences changes when, and whether, element functions run; this matters when they have effects, throw, or read changing state.
- **Short-circuiting lost.** An index built from all elements evaluates elements the original never touched, possibly throwing or doing I/O. Reordering `&&`, `||`, or a chain of checks to test the cheap one first changes which calls run and which error is raised.
- **Deferred queries.** LINQ and ORM query objects re-execute on each enumeration; materializing or caching them changes when data is read.
- **Key functions.** A comparator runs per comparison and never on a one-element input; computing keys up front runs the key on every element, once, in a different order. A key that can throw, has effects, or is not deterministic now behaves differently, including on inputs of size one.
- **Moved reads.** Reading a property once before a loop stops seeing changes made during it. Extracting code into a function turns reads into arguments, evaluated at the call, so a clock, configuration value, or shared field read midway through the original is read earlier unless the extraction keeps that point.

## Numbers

For numerical code, test the edge values in `DIFFERENTIAL-TESTING.md`; ordinary inputs rarely expose these.

- **Overflow.** A closed form, a narrower type, or a rearranged formula can overflow (or underflow to zero) where the loop did not, including in an intermediate step whose final result fits. Some languages wrap silently, others trap. In sizes, offsets, and money, a wrapped value is also a security or money bug.
- **Float association and reproducibility.** `(a + b) + c` is not `a + (b + c)`: prefix sums, reordering, parallel reduction, vectorization, and fused multiply-add change bits, and can differ across runs and machines. A flag like `-ffast-math` reorders and contracts float operations across the whole build; adding it is a configuration change (rule 5).
- **Catastrophic cancellation.** Expanding or factoring a formula can subtract nearly equal values and lose most significant digits.
- **Rounding and division.** Rewritten arithmetic can round differently (Python rounds half to even). Integer division by zero traps; float division gives infinity or NaN. Float-to-integer conversion truncates, saturates (Rust), traps (Swift), or is undefined (C). Moving arithmetic between integer and float changes all of these.
- **NaN and signed zero.** NaN propagates differently through min, max, comparisons, and sorting; `-0.0` equals `0.0` but differs in division and formatting.
- **Bit width.** Shifts beyond the type width, signed versus unsigned shifts, and 32-bit limits in some runtimes.
- **Exact versus tolerance.** Switching between exact equality and a tolerance changes results.

## Strings and text

- **Length, indexing, and order units.** UTF-16 code units, code points, and grapheme clusters give different lengths and indices. Sort order differs too: UTF-16 order (JavaScript's default sort, Java's `compareTo`, C#'s ordinal comparison), code-point or UTF-8 byte order (Python, Rust), and culture-aware order (C#'s default string comparison and sort, `localeCompare`, collators) disagree, the first two outside the basic multilingual plane and culture-aware order almost everywhere.
- **Case, culture, and normalization.** Locale-dependent case conversion and comparison (Turkish dotted and dotless `i`) and number and date formatting. Lowercasing is not case folding (`ß` uppercases to `SS`), and composed and decomposed forms compare unequal unless normalized. A new structure or comparison must use the same comparer, and normalizing, folding, or comparing bytes where the original did not changes which strings match.
- **Parsers and character classes.** A different parser or regex engine accepts a different set: non-ASCII digits (many integer parsers and Unicode-aware `\d` accept Arabic-Indic digits), surrounding whitespace, `+`, underscores, hex prefixes, leading zeros, overlong input. Accepting more is also a validation change.
- **Serialized output.** A different serializer or number formatter changes key order, float text (`1.0` vs `1`, `1e21`), escaping, whitespace, and line endings, and so anything that diffs, hashes, signs, or caches by content.

## Time and dates

Interval semantics (inclusive ends, touching intervals, ranges across midnight) are in "Pin down time and intervals" in `techniques/optimization-and-scheduling.md`.

- **Calendar arithmetic.** 86,400 seconds is not a day across DST. Precomputed day or month boundaries, bucketing in UTC instead of local time, and fixed month or year lengths go wrong around DST, leap days, and time-zone rule changes. Test across those boundaries in the zones the code uses.
- **Clocks.** Wall-clock time jumps; timing durations with it instead of a monotonic clock, or caching "now" or "today" longer than the original read it, changes results.

## Removed work

Work that looks unnecessary often is not:

- **Unseen callers.** Results unused inside the repository may be used through a public API, an endpoint, a plugin interface, reflection, dependency injection, serialization, configuration, or templates. For public or exported code, treat every result as used.
- **Validation by side effect.** A computation with a discarded result may exist to throw on bad input.
- **Reads with effects.** Device registers, memory-mapped I/O, `volatile` variables, page touches, and lazy initialization on first access.
- **Deliberate timing and ordering.** Constant-time padding, delays and backoff, memory fences, lock acquisitions that order other threads, and warm-up look like waste. Removing them is a security or correctness regression.
- **Logs, metrics, and audit records.** A cache hit, batch, or skip also skips, merges, or reorders the record the original wrote each time; audit records may be legally required. Logging values that were not logged before can leak data. Making logging lazy stops evaluating its arguments when the level is off, which matters when building them has effects.
- **"Nothing changed."** Skipping a refresh because inputs look unchanged is caching, with all the traps below.

## Purity and caching

### Hidden inputs

Unchanged arguments do not make a function pure. Before caching, rule out dependence on: time, time zone, or calendar; locale; environment variables, feature flags, configuration, or experiment assignment; files, network, or other external state; randomness or nondeterministic iteration order; the current user, tenant, session, or permissions; process-specific state (process ID, addresses, hash seeds).

### Caching traps

- **Memoizing the impure.** Any hidden input above, mutable state, or the database makes cached results stale or wrong.
- **Scope and invalidation.** A cache scoped wider than its data's lifetime (process-wide instead of per call or per object) serves stale data and leaks across users. It must be invalidated whenever any input it depends on changes.
- **Writers outside this process.** Invalidating on local writes misses other workers, machines, import jobs, and admin scripts that share the data. Where any can exist, as deployment or configuration shows, the cache must check a version number or change counter that the shared source maintains on every read and refetch when it moved, or cache only data those writers never change.
- **Eviction.** A bounded cache changes which calls take the slow path; fine only for a pure function.
- **Keys that collide or never match.** Concatenated keys collide (`"a:" + "b"` equals `"a" + ":b"`), stringified arguments drop `undefined` or depend on property order, and object keys compare by reference so equal arguments never hit. Build keys from a tuple of the arguments.
- **Cached failures.** Caching an exception or empty result turns a transient failure the original retried into a permanent one; decide and state which is cached.

## Concurrency

- **Thread safety.** Swapping a concurrent structure for an unsynchronized one, or adding a shared cache, introduces races wherever the code runs on several threads or workers (request handlers usually do). Shared state you add needs synchronization and a concurrent test, under a race detector or thread sanitizer where one exists; a lock no test exercises concurrently is unverified.
- **Iterator invalidation.** Modifying a collection while iterating it throws, skips elements, or is undefined behavior (C, C++).
- **Changed concurrency.** Making sequential work concurrent changes ordering, error behavior (fail-fast or continue), rate limiting, and resource use.
- **Optimistic and speculative execution.** A lock-free reader (sequence locks, optimistic concurrency) can see torn data before validating and must not act on it first: no dereference, division, index, or output. A retry repeats every side effect of the attempt, and speculative work for a wrong guess must leave no trace.
- **Missed changes.** Switching from rescans to change feeds, file-system notifications, or incremental maintenance misses updates when the feed overflows, restarts, or is truncated. Detect every gap and fall back to a full rescan.

## Cancellation, timeouts, and resources

These change production behavior while tests still return the same values:

- **Cancellation.** Batched or parallel work can ignore cancellation the per-item loop honored, or cancel more than before.
- **Timeouts.** One timeout around a batch lets a slow item fail the whole batch.
- **Partial failure.** One failed item can fail a batch where the loop processed the rest, and cleanup and rollback must still run when only part succeeds.
- **Resource lifetimes.** Handles, connections, streams, and locks are held longer or released earlier when work is batched, cached, or made lazy.
- **Locks and pools.** Changing lock order or holding a lock across more work can deadlock or starve; more concurrency can exhaust pools sized for sequential use.
- **Moved work.** Precomputing at load time changes startup time, memory in processes that never call the code, and where errors surface (a missing file fails process start instead of one call). Lazy initialization moves cost and errors to the first call and needs thread-safe initialization.

## Security-sensitive behavior

These are security regressions, not optimizations, however much faster they are. "Optimizations that weaken a defense" in `techniques/hostile-inputs.md` covers revocation delay, parser differentials, path handling, and overflow in sizes.

- **Constant-time code.** Early-exit or data-dependent replacements for comparisons of secrets, tokens, MACs, or password hashes.
- **Authorization and validation.** Early exits, caching, batching, or reordering that skip, reorder, or weaken authentication, authorization, or input checks.
- **Query building.** A batched `WHERE id IN (...)` keeps values as bound parameters and chunks to the driver's parameter limit.
- **Cache keys.** A key missing user, tenant, permission, locale, or configuration context leaks data across callers.
- **Worst-case blowups.** A better average with a much worse worst case is a denial-of-service risk: hash flooding on attacker-chosen keys (use worst-case structures or keyed hashing), unbounded caches, quadratic paths on crafted input, unbounded recursion, regular expressions built from input or prone to backtracking.
- **Approximate structures.** Bloom filters, sketches, and probabilistic counters are wrong sometimes; where the answer decides access, money, payment deduplication, or a security check, exactness is part of the contract.
- **Random sources.** A faster or seeded generator in place of a cryptographic one for anything an attacker must not predict: tokens, session and reset identifiers, salts, nonces, shuffles that decide money.
- **Limits, retries, and records.** Raising or removing a rate, queue, pool, size, or depth limit; recursion depth controlled by input; retrying operations that are not idempotent; disabling hash randomization or certificate checks; reusing buffers without clearing them; a cache that never invalidates; logging data that was not logged before.

An existing weakness is a bug to report (rule 4).

## Errors and limits

- **Different exceptions.** A new structure may throw a different type, at a different point, or not at all. With several bad inputs, a reordered, batched, or parallel version may report a different one first, or all of them, and the work done before the error may differ.
- **Non-throwing variants.** A non-throwing parse or a check made first can accept a different set of inputs from the call that threw, and whatever the catch block logged or counted no longer happens unless it is kept.
- **New size limits.** An optimization valid only up to a size the original never limited (a 64-bit mask, a table sized for test data, a fixed buffer, more memory than the original needed) adds an error or wrong result above it. Check the largest size callers can pass, not the sizes in tests.
- **Recursion depth.** Turning iteration into recursion introduces stack overflow on large valid input, which is a regression. Removing an existing overflow removes a bug: the version that removes it needs the developer's approval by name (rule 4 in "Rule details" in `WORKFLOW.md`).
- **Cycles.** A recursive walk over linked data that contains a cycle fails fast with a stack overflow; an iterative rewrite without a visited set or depth bound loops forever or exhausts memory instead. Keep a visited set or a bound that fails the same way, even if the data "should" be acyclic.

## I/O and databases

- **Transactions.** Batching queries changes transaction boundaries, locking, and what a concurrent writer can interleave.
- **Result order.** Without `ORDER BY` rows come in no guaranteed order, and a batched `IN` query can order them differently from per-item queries.
- **Read-after-write.** A per-item loop's later reads see its earlier writes (a repeated key, a value derived from a previous item); a batched read taken before the writes does not.
- **Buffering.** Buffering per-line writes changes when output appears, how it interleaves with other streams, what a pipe reader sees before the end, and what survives a crash. Keep the original's flush points.
