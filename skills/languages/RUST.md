# Rust

Record the toolchain, edition, and minimum supported Rust version (`rust-version` in `Cargo.toml`); several APIs below were stabilized in specific versions. A `no_std` crate has no `std::collections`: `alloc` still provides `Vec`, `VecDeque`, `BTreeMap`, `BinaryHeap`, but not `HashMap`.

**Contents:** Built-in structures · Hidden costs · Bit manipulation · Rust-specific traps · Testing and benchmarking · References

## Built-in structures

| Structure | API | Key costs | Notes |
|---|---|---|---|
| Growable array | `Vec<T>` | index O(1), `push` amortized O(1), `insert(0, x)`/`remove(0)` O(n), `contains` O(n) | `with_capacity` avoids reallocation |
| Double-ended queue | `VecDeque<T>` | both ends O(1) amortized | Queues, BFS |
| Hash map / set | `HashMap`, `HashSet` | O(1) expected | SipHash default resists flooding but is slower; iteration order is randomized per map (each `RandomState`), so two maps with equal contents usually iterate differently in one process |
| Ordered map / set | `BTreeMap`, `BTreeSet` | O(log n); `range`, `first_key_value`, `last_key_value` | Sorted iteration |
| Priority queue | `BinaryHeap<T>` | `push` O(1) expected, O(log n) amortized (a single push costs O(n) when the backing vector grows); `pop` O(log n); `peek` O(1) | Max-heap; `std::cmp::Reverse` for min; no decrease-key |
| Linked list | `LinkedList<T>` | O(1) at ends | Rarely right |
| String building | `push_str`, `write!`, `concat`, `join` | amortized O(1) per byte | |
| Slice algorithms | `sort` (stable), `sort_unstable`, `sort_by_key`, `binary_search`, `select_nth_unstable`, `partition_point`, `chunks`, `windows`, `retain`, `dedup`, `swap_remove` (O(1)) | | `select_nth_unstable` is O(n) worst case in recent releases; older documentation says O(n log n), so check against `rust-version` |
| Lazy iterators | `iter()`, `map`, `filter`, `take_while` | No intermediate allocation | Run only when consumed |
| Lazy statics | `LazyLock` (1.80+), `OnceLock` (1.70+) | One-time initialization | |

Not in the standard library: bitsets, insertion-ordered maps, LRU caches, fast non-cryptographic hashers, small vectors, tries, segment trees, concurrent maps (`fixedbitset`, `bitvec`, `indexmap`, `lru`, `rustc-hash`, `ahash`, `smallvec`, `arrayvec`, `dashmap` are dependencies).

### Packages

These are dependencies (rule 7): check the module's manifest first, and follow "When the best technique is not available" in `ALGORITHM-ARSENAL.md`. The crates named above are also dependencies.

| Package | Provides | Watch for |
|---|---|---|
| `itertools` | `k_smallest` (ascending; memory proportional to k), `sorted_by_cached_key`, `unique` | `dedup` removes only consecutive duplicates. `sorted_unstable` may reorder equal elements |
| `slotmap` | `SlotMap`, `DenseSlotMap`: O(1) insert, access, and delete with stable keys | A key used on another map gives an unspecified result. `SlotMap` iteration scans empty slots; `DenseSlotMap` is contiguous. `HopSlotMap` is deprecated |

## Hidden costs

| Pattern | Cost | Fix |
|---|---|---|
| `vec.contains(&x)` in a loop | O(n·m) | `HashSet` once (ordering trap) |
| `remove(0)` or `insert(0, x)` as a queue | O(n) per operation | `VecDeque` |
| `s.chars().nth(i)` in a loop | O(i) per call, O(n²) total | Iterate once, collect `chars()` once, or byte indices when semantics allow (`&s[..n]` and `split_at` panic off a char boundary: use `is_char_boundary` or `get(..n)`) |
| `s.chars().count()` in a loop condition | O(n) each time | Compute once (`s.len()` is bytes) |
| `.clone()` of large values in loops | Allocation and copying | Borrow, `Rc`/`Arc`, or move |
| `collect::<Vec<_>>()` only to iterate again | Intermediate allocation | Chain the iterator |
| `format!`/`to_string()` in hot loops | Allocation per call | `write!` into a reused `String` |
| `sort_by_key(\|x\| parse(x))` | Named like a keyed sort, but the key runs per comparison: O(m·n log n) | `sort_by_cached_key`, which calls it at most once per element, O(m·n + n log n), and is also stable. Not needed for a cheap field read |
| `.to_vec()` of a slice in recursion | Copies each call: O(n²) | Pass `&a[1..]`, a view |
| `#[derive(Hash)]` on a key holding a `Vec` or many fields | Hashes every field on each hash | A small ID or a narrower key type |
| `get(k)` then `insert(k, ...)` | Two lookups | `entry` API |
| `Regex::new` in a loop or hot function | Recompiles | `LazyLock<Regex>` or `OnceLock` |
| `println!` in a hot loop | Locks stdout, flushes lines | Lock once and wrap in `BufWriter` (a behavior change for interactive output or on crash: "Buffering" in `BEHAVIOR-TRAPS.md`) |
| Unbuffered file reads | A system call per small read | `BufReader` |
| `Vec` growing when the size is known | Repeated reallocation | `with_capacity`/`reserve`; cap a size that comes from input, since it aborts on allocation failure or panics on overflow |
| Indexing in hot loops | Bounds checks can block vectorization | Iterators, `chunks_exact`, or slicing once so checks are elided |
| `Rc<RefCell<T>>`, `Arc<Mutex<T>>` graphs in hot paths | Refcounting, runtime borrow checks, contention | Index-based arenas |
| `Box<dyn Trait>` in hot loops | Dynamic dispatch, no inlining | Generics or enums, if the contract allows |

### Input handling and security

- **Number parsing.** `str::parse` for integers accepts ASCII digits with an optional `+` or `-` only (no whitespace, underscores, or `0x`) and returns `Err` on overflow. Float parsing also accepts `inf`, `infinity`, and `NaN` in any case. `char::is_numeric` is true for non-ASCII digits; `is_ascii_digit` is not.
- **`as` casts never fail.** Integer narrowing truncates; float-to-integer saturates (NaN becomes 0). Replacing `try_from` with `as` for speed turns an error into a wrong value.
- **Regular expressions.** The `regex` crate is linear time but limits compiled size, so a pattern built from input can fail to compile; `fancy-regex` and `pcre2` backtrack. Escape input with `regex::escape`.
- **Stack overflow aborts the process** (8 MB main thread on typical Linux, 2 MiB default for spawned threads); it is not a catchable panic. `serde_json` limits nesting to 128 by default; keep that limit.
- **Case conversion** (`to_uppercase`, `to_lowercase`) is Unicode-aware, locale-independent, and can change length (`"ß"` to `"SS"`); `to_ascii_uppercase` touches only ASCII.

## Bit manipulation

| Operation | Rust |
|---|---|
| And, or, xor, not, shifts | `&`, `\|`, `^`, `!`, `<<`, `>>` (arithmetic for signed, logical for unsigned) |
| Popcount, trailing / leading zeros | `count_ones()`, `trailing_zeros()`, `leading_zeros()` |
| Power of two, rotation | `is_power_of_two()`, `next_power_of_two()`, `rotate_left`, `rotate_right` |
| Explicit overflow | `wrapping_*`, `checked_*`, `overflowing_*`, `saturating_*`; `checked_shl` |

Shifting by at least the bit width panics in debug builds and masks the count in release; use `wrapping_shl` or `checked_shl` when the count may be large.

## Rust-specific traps

- **Debug and release overflow differ.** Overflow panics in debug and wraps in release (unless `overflow-checks` is on), so a closed form that overflows where the loop did not can pass tests and wrap in production. Match the original with explicit `wrapping_*`/`checked_*`.
- **Hash iteration order is randomized per map:** a `HashMap` cannot replace a structure whose iteration order the original exposed, and two maps do not iterate in step.
- **Changing the hasher** (`FxHashMap`, `ahash`) changes iteration order and removes flooding resistance: a security regression for user-controlled keys, and a dependency.
- **Sort stability:** `sort`, `sort_by_key` stable; `sort_unstable` not.
- **`dedup` removes only consecutive duplicates.**
- **`binary_search` may return any matching index;** `partition_point` gives the first or last.
- **`swap_remove` changes element order.**
- **Floats are not `Ord`.** `partial_cmp(...).unwrap()` panics on NaN, while `total_cmp` orders NaN and `-0.0` differently.
- **Drop order and RAII.** Caching values or extending lifetimes changes when destructors run: when locks release, files flush, guards end. Guards held longer can deadlock.
- **Laziness.** Iterator adapters run closures only when consumed, element by element; converting between eager loops and lazy chains changes the order and number of side effects.
- **Panics versus errors:** keep whether the code panics, returns `Err`, or returns `None` in each case.
- **`unsafe` is not an optimization by default.** `get_unchecked`, `set_len`, raw pointers, or `transmute` for speed need the developer's approval, a written safety argument, and tests under Miri.
- **Parallelism and async.** `rayon` (a dependency), threads, `join_all`, and `select!` change side-effect order, cancellation, errors, and floating-point reduction results.

## Testing and benchmarking

- **Tests:** `cargo test`, including doc tests. `cargo build`, `check`, and `test` run every `build.rs` and procedural macro in the project and its dependencies, and `.cargo/config.toml` can set runners and wrappers.
- **Testing an extracted function:** a private function tested from a child `#[cfg(test)]` module, which can see its parent's private items; `pub(crate)` if tests live elsewhere in the crate.
- **Property-based testing and fuzzing, if already present:** `proptest`, `quickcheck`, `cargo fuzz`; otherwise a small seeded generator (`rand` as a dev-dependency is still a dependency).
- **Miri** (`cargo +nightly miri test`) whenever `unsafe` is involved.
- **Profiling:** `perf` with `cargo flamegraph` or samply (installs), or Instruments; set `debug = "line-tables-only"` under `[profile.release]` for symbols without changing optimization.
- **Benchmarks:** `criterion` or `divan` if present; otherwise `std::time::Instant` with `std::hint::black_box` (1.66+), built with `--release`. Memory: `dhat` (a dependency), heaptrack, Massif.
- **Verification beyond tests** ("Verification levels" in `DIFFERENTIAL-TESTING.md`): Kani (`#[kani::proof]` harnesses, including old-versus-new equivalence over bounded inputs); loom (every thread interleaving up to a bound); Verus, Prusti, Creusot for contracts.
- **Constant-time comparison:** the `subtle` crate's `ConstantTimeEq` (a dependency), not `==` on secret slices.

## References

Sources: `references/languages/RUST.md`.
