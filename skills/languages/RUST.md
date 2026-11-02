# Rust

Load this file for Rust projects. Record the toolchain, the edition, and the minimum supported Rust version (`rust-version` in `Cargo.toml`): several standard-library APIs below were stabilized in specific versions. Check whether the crate is `no_std`, which removes `std::collections` (`alloc` still provides `Vec`, `VecDeque`, `BTreeMap`, `BinaryHeap`, but not `HashMap`).

## Built-in structures

| Structure | API | Key costs | Notes |
|---|---|---|---|
| Growable array | `Vec<T>` | index O(1), `push` amortized O(1), `insert(0, x)`/`remove(0)` O(n), `contains` O(n) | `with_capacity` avoids reallocations |
| Double-ended queue | `VecDeque<T>` | push/pop at both ends O(1) amortized | Use for queues and BFS |
| Hash map / set | `HashMap`, `HashSet` | O(1) expected | Default hasher (SipHash) resists hash flooding but is slower; **iteration order is randomized per process** |
| Ordered map / set | `BTreeMap`, `BTreeSet` | O(log n); `range`, `first_key_value`, `last_key_value` | Sorted iteration |
| Priority queue | `BinaryHeap<T>` | `push` O(1) expected, O(log n) worst; `pop` O(log n); `peek` O(1) | **Max-heap**; wrap in `std::cmp::Reverse` for a min-heap; no decrease-key |
| Linked list | `LinkedList<T>` | O(1) at ends | Rarely the right choice |
| String building | `String::push_str`, `write!`, `concat`, `join` | amortized O(1) per byte | |
| Slice algorithms | `sort` (stable), `sort_unstable`, `sort_by_key`, `binary_search`, `select_nth_unstable` (O(n) expected), `partition_point`, `chunks`, `windows`, `retain`, `dedup`, `swap_remove` (O(1)) | | See traps |
| Lazy iterators | `iter()`, `map`, `filter`, `take_while` | No intermediate allocation | Evaluate only when consumed |
| Lazy statics | `std::sync::LazyLock`, `OnceLock` | One-time initialization | `LazyLock` stable since 1.80; `OnceLock` since 1.70 |

**Not in the standard library:** bitsets, ordered-by-insertion maps, LRU caches, faster non-cryptographic hashers, small-vector optimizations, tries, segment trees, concurrent maps. Common crates (`fixedbitset`, `bitvec`, `indexmap`, `lru`, `rustc-hash`, `ahash`, `smallvec`, `arrayvec`, `dashmap`) are dependencies: ask first (rule 7). A small structure inside the project (a bitset over `Vec<u64>`, a ring buffer) is not a dependency but needs its own tests.

## Hidden costs

This table lists common traps, not every operation. Every call counts at its real cost, including ones not listed here ("Count every call at its real cost" under rule 6 in `SKILL.md`).

| Pattern | Cost | Fix |
|---|---|---|
| `vec.contains(&x)` inside a loop | O(n·m) | `HashSet` built once (check the ordering trap) |
| `vec.remove(0)` or `insert(0, x)` as a queue | O(n) per operation | `VecDeque` |
| `s.chars().nth(i)` inside a loop | O(i) per call, O(n²) total | Iterate once, or collect `chars()` once, or use byte indices when the semantics allow |
| `s.chars().count()` in a loop condition | O(n) each time | Compute once (note `s.len()` is bytes, not characters) |
| `.clone()` of large values inside loops | Allocation and copying | Borrow, use `&T`, `Rc`/`Arc`, or move |
| `collect::<Vec<_>>()` only to iterate again | Intermediate allocation | Chain the iterator directly |
| `format!`/`to_string()` in hot loops | Allocation per call | Write into a reused `String` with `write!` |
| `map.get(k)` followed by `map.insert(k, ...)` | Two lookups | `entry` API |
| `Regex::new` inside a loop or hot function | Recompiles each time (regex crate) | `LazyLock<Regex>` or `OnceLock` |
| `println!` in a hot loop | Locks stdout and flushes lines | Lock `stdout` once and wrap it in `BufWriter` |
| Reading files without buffering | One system call per small read | `BufReader` |
| `Vec` growing without a size hint when the size is known | Repeated reallocations | `with_capacity` or `reserve` |
| Indexing in hot loops with bounds checks | Bounds checks can block vectorization | Iterators, `chunks_exact`, or slicing once so the compiler can elide checks. Never `get_unchecked` without asking (see traps) |
| `Rc<RefCell<T>>` or `Arc<Mutex<T>>` graphs in hot paths | Reference counting, runtime borrow checks, lock contention | Index-based arenas or ownership restructuring |
| `Box<dyn Trait>` in hot loops | Dynamic dispatch, no inlining | Generics or enums, if the contract allows |

## Bit manipulation

| Operation | Rust |
|---|---|
| And, or, xor, not, shifts | `&`, `\|`, `^`, `!`, `<<`, `>>` (arithmetic for signed, logical for unsigned) |
| Popcount | `x.count_ones()` |
| Trailing / leading zeros | `x.trailing_zeros()`, `x.leading_zeros()` |
| Power of two | `x.is_power_of_two()`, `x.next_power_of_two()` |
| Rotation | `x.rotate_left(n)`, `x.rotate_right(n)` |
| Explicit overflow handling | `wrapping_*`, `checked_*`, `overflowing_*`, `saturating_*`; `checked_shl` for shifts |

Shifting by a count greater than or equal to the bit width panics in debug builds and masks the count in release builds. Use the explicit `wrapping_shl` or `checked_shl` when the count may be large.

## Rust-specific traps

- **Debug and release overflow behavior differ.** Integer overflow panics in debug builds and wraps in release builds (unless `overflow-checks` is enabled). A closed-form formula that overflows where the loop did not can panic in tests and silently wrap in production. Match the original's behavior with the explicit `wrapping_*`/`checked_*` operations it implied.
- **`HashMap`/`HashSet` iteration order is randomized per process.** Never iterate them where the original exposed a deterministic order.
- **Changing the hasher** (for example to `FxHashMap` or `ahash`) changes iteration order and removes hash-flooding resistance. For keys controlled by users or attackers, that is a security regression (see `BEHAVIOR-TRAPS.md`). It also needs a dependency.
- **Sort stability.** `sort` and `sort_by_key` are stable; `sort_unstable` is not. Switching changes the order of equal elements.
- **`dedup` removes only consecutive duplicates.** It is not equivalent to deduplicating with a set unless the input is sorted.
- **`binary_search` may return any matching index** among duplicates. Use `partition_point` when the original returned the first or last match.
- **`swap_remove` changes element order.**
- **Floats are not `Ord`.** `sort_by(|a, b| a.partial_cmp(b).unwrap())` panics on NaN, while `total_cmp` orders NaN and `-0.0` differently. Switching between them is a behavior change.
- **Drop order and RAII.** Restructuring code, caching values, or extending lifetimes changes when destructors run: when locks are released, files are flushed, or guards end. Lock guards held longer can cause deadlocks.
- **Laziness.** Iterator adapters run closures only when consumed, element by element. Converting between eager loops and lazy chains changes the order and number of side effects.
- **Panics versus errors.** A rewrite must panic, return `Err`, or return `None` in exactly the same cases as the original.
- **`unsafe` is never an optimization by default.** Do not introduce `unsafe` (for example `get_unchecked`, `set_len`, raw pointers, `transmute`) to gain speed without the developer's explicit approval, a written safety argument, and tests under Miri where possible.
- **Parallelism.** Moving to `rayon` (a dependency) or threads changes the order of side effects and floating-point reduction results.
- **Async.** Replacing sequential `.await`s with `join_all` or `select!` changes ordering, cancellation, and error behavior.

## Testing and benchmarking

- **Tests:** `cargo test`; doc tests count as tests.
- **Property-based testing and fuzzing, if already present:** `proptest`, `quickcheck`, `cargo fuzz`. Otherwise use a small seeded generator in test code; adding `rand` as a dev-dependency is still a dependency, so ask.
- **Undefined behavior checks:** run tests under Miri (`cargo +nightly miri test`) whenever `unsafe` code is involved.
- **Profiling:** `perf` with `cargo flamegraph` or samply (installs), or Instruments on macOS; set `debug = true` (or `debug = "line-tables-only"`) under `[profile.release]` for symbols, without changing optimization.
- **Benchmarks:** use `criterion` or `divan` if already present (both are dependencies otherwise; ask). Without them, write a timing harness with `std::time::Instant` and `std::hint::black_box` (stable since 1.66) to stop the compiler from removing work. Always benchmark with `--release`.
- **Memory:** `dhat` (a dependency), heaptrack, or Valgrind Massif for peak heap and allocation counts.
- **Verification beyond tests** (see "Verification levels" in `DIFFERENTIAL-TESTING.md`; dependencies or installs, so ask unless present): Kani for bounded model checking with `#[kani::proof]` harnesses, including equivalence of the old and new function over bounded inputs; loom to run concurrent code under every thread interleaving up to a bound; Verus, Prusti, or Creusot for proofs of contracts.
- **Constant-time comparison** (for secrets; see `techniques/hostile-inputs.md`): the `subtle` crate's `ConstantTimeEq` (a dependency, so ask unless present), never `==` on secret slices.

## References (for verifying claims; not required reading)

- Rust collections, with a table of operation costs: doc.rust-lang.org/std/collections/index.html
