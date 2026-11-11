# Sources for `skills/algorithmic-intelligence/references/languages/RUST.md`

Where each claim in that file comes from, for maintainers and reviewers. Not part of the installed skill. Standard library pages are under doc.rust-lang.org/std/ followed by the path given. Source paths are in github.com/rust-lang/rust.

## Built-in structures

- Costs of every collection, in one table: `collections/index.html` ("Performance").
- `no_std` and what `alloc` provides: doc.rust-lang.org/alloc/ (module list; no `HashMap`).
- `HashMap` default hasher (SipHash 1-3) and per-map `RandomState` seeding: `collections/struct.HashMap.html` and `hash/struct.RandomState.html`.
- `BTreeMap` (`range`, `first_key_value`, `last_key_value`): `collections/struct.BTreeMap.html`.
- `BinaryHeap` push and pop costs, including the O(n) push on growth: the cost table in `collections/struct.BinaryHeap.html`.
- Slice sorting, stability, `select_nth_unstable` worst case, `partition_point`, `swap_remove`: `primitive.slice.html` (each method's section); `select_nth_unstable`'s O(n) worst case is stated in recent releases' documentation, while older releases' documentation says O(n log n); compare the page for the project's version.
- `LazyLock` (1.80) and `OnceLock` (1.70): `sync/struct.LazyLock.html` and `sync/struct.OnceLock.html`.

## Packages

- itertools (`k_smallest`, `sorted_by_cached_key`, `unique`, `dedup`, `sorted_unstable`): docs.rs/itertools (the `Itertools` trait page).
- slotmap (`SlotMap`, `DenseSlotMap`, keys used on another map, `HopSlotMap` deprecation): docs.rs/slotmap (crate front page and each type).
- Release dates: crates.io/crates/<name>.

## Hidden costs

- `chars().nth` iterating from the start: `iter/trait.Iterator.html#method.nth`. Slicing a `str` off a char boundary panics: `primitive.str.html` ("Panics" under slicing) and `primitive.str.html#method.is_char_boundary`.
- `sort_by_key` calling the key per comparison and `sort_by_cached_key` (at most once per element, O(m·n + n log n), stable): `primitive.slice.html#method.sort_by_key` and `#method.sort_by_cached_key`.
- `to_vec` copying: `primitive.slice.html#method.to_vec`. `derive(Hash)` hashing every field: `hash/trait.Hash.html` ("Implementing Hash").
- `entry` API: `collections/hash_map/enum.Entry.html`.
- `println!` locking stdout, and stdout being line-buffered: `io/struct.Stdout.html`. `BufWriter`, `BufReader`: `io/struct.BufWriter.html`, `io/struct.BufReader.html`.
- `Vec::with_capacity` panicking on capacity overflow and aborting on allocation failure: `vec/struct.Vec.html#method.with_capacity` and `alloc/fn.handle_alloc_error.html`.

## Input handling and security

- Integer `FromStr` (sign, ASCII digits, overflow errors): `primitive.i64.html#method.from_str_radix` and `num/struct.ParseIntError.html`. Float `FromStr` accepting `inf`, `infinity`, `nan` in any case: `primitive.f64.html#impl-FromStr-for-f64`. `char::is_numeric`: `primitive.char.html#method.is_numeric`.
- `as` casts (truncation, saturating float-to-integer, NaN to 0): The Rust Reference, "Type cast expressions" (doc.rust-lang.org/reference/expressions/operator-expr.html#type-cast-expressions).
- regex crate linear time and its compiled-size limit; `regex::escape`: docs.rs/regex (sections "Untrusted input" and `RegexBuilder::size_limit`).
- Stack overflow aborting, and the 2 MiB default for spawned threads: `thread/index.html` ("Stack size"). serde_json's recursion limit of 128: docs.rs/serde_json (`Deserializer::disable_recursion_limit`).
- Case conversion: `primitive.str.html#method.to_uppercase` and `#method.to_ascii_uppercase`.

## Bit manipulation and traps

- Bit methods (`count_ones`, `trailing_zeros`, `is_power_of_two`, `rotate_left`, `wrapping_*`, `checked_shl`): `primitive.u64.html`.
- Overflow panicking in debug and wrapping in release, and the same for shift amounts: The Rust Reference, "Arithmetic and Logical Binary Operators" and "Overflow" (doc.rust-lang.org/reference/expressions/operator-expr.html#overflow); Cargo profile setting `overflow-checks` (doc.rust-lang.org/cargo/reference/profiles.html#overflow-checks).
- `binary_search` returning any match: `primitive.slice.html#method.binary_search`. `dedup` removing consecutive duplicates: `vec/struct.Vec.html#method.dedup`.
- `partial_cmp` and `total_cmp`: `primitive.f64.html#method.total_cmp`.
- Drop order: The Rust Reference, "Destructors" (doc.rust-lang.org/reference/destructors.html).
- `unsafe` obligations: The Rustonomicon (doc.rust-lang.org/nomicon/).

## Testing and benchmarking

- Build scripts and procedural macros running at build time: doc.rust-lang.org/cargo/reference/build-scripts.html and doc.rust-lang.org/reference/procedural-macros.html. `.cargo/config.toml` runners: doc.rust-lang.org/cargo/reference/config.html.
- Testing private functions from a child module: doc.rust-lang.org/book/ch11-03-test-organization.html.
- Miri: github.com/rust-lang/miri. `debug = "line-tables-only"`: doc.rust-lang.org/cargo/reference/profiles.html#debug. `std::hint::black_box` (1.66): `hint/fn.black_box.html`.
- Kani and equivalence harnesses: model-checking.github.io/kani. loom: docs.rs/loom. Verus: github.com/verus-lang/verus. Prusti: github.com/viperproject/prusti-dev. Creusot: github.com/creusot-rs/creusot.
- `subtle::ConstantTimeEq`: docs.rs/subtle.
