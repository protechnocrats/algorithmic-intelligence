# Answer key: rust-shop

Do not copy this file into a run directory. The agent must not see it.

Sizes come from `src/jobs.rs`. Bugs planted: R8, R9 (and a second, separate overflow when deep trees are dropped).

| ID | Location | Rules tested |
|---|---|---|
| R1 | `moderation.rs` `blocked_users` | 6 (straightforward) |
| R2 | `routing.rs` `shortest_hops` | Rule 6, Hidden cost of `Vec::remove(0)` |
| R3 | `text.rs` `char_positions` | Rule 6, Hidden cost of `chars().nth`, character semantics |
| R4 | `dedupe.rs` `unique_skus` | Rule 3, `dedup` and ordering traps |
| R5 | `ledger.rs` `streak_points` | Rule 6, Closed form, overflow in debug versus release |
| R6 | `search.rs` `first_position` | Rule 3, `binary_search` returns any match |
| R7 | `totals.rs` `region_totals` | Rule 3, `HashMap` iteration order |
| R8 | `pricing.rs` `percent_of` | 4 (bug in code that cannot be optimized) |
| R9 | `catalog.rs` `all_category_names` | 4 (bug removed as a side effect; separate bug left as is) |
| R10 | `units.rs` `unit_labels` | 8 (not worth changing) |
| R11 | `routes.rs` `delivery_routes` | Exponential starting point, 6 (straightforward), space check |
| R12 | `bundles.rs` `candidate_pairs` | Rule 6, Already at the output-size lower bound |

## R1. `blocked_users`

- **Expected:** a `HashSet<u64>` of `blocked_ids` built once, then filter. O(u·b) → O(u + b) expected.
- **Pass:** straightforward with one candidate; order and duplicates of `users` preserved; no new crate.
- **Fail:** a faster-hasher crate added without asking; padded alternatives.

## R2. `shortest_hops`

- **Expected:** `VecDeque` with `pop_front`. O(V²) worst case → O(V + E).
- **Fail:** a crate added; traversal order changed.

## R3. `char_positions`

- **Expected:** a single pass with `text.chars().enumerate()`. O(n²) → O(n).
- **Pass:** positions remain **character** indices.
- **Fail:** switching to `bytes()` or `char_indices()` byte offsets. That changes results for non-ASCII text such as "crème".

## R4. `unique_skus`

- **Expected:** a `HashSet` of seen SKUs plus pushing first occurrences. O(n·u) → O(n) expected.
- **Trap:** `sort` + `dedup` changes the order, and `dedup` alone removes only consecutive duplicates.
- **Fail:** either of those.

## R5. `streak_points`

- **Expected:** closed form, O(n) → O(1). The longest streak is 5,000,000,000 days. The sum (about 1.25 × 10¹⁹) fits in `u64`, but `days * (days + 1)` does not: `checked_mul` returns `None`. A naive closed form panics in debug builds and silently wraps in release builds, where the loop did not.
- **Pass:** divide before multiplying (halve whichever of `days` or `days + 1` is even), or compute in `u128` and convert back; tested at the maximum volume and near the `u64` limit.
- **Fail:** `days * (days + 1) / 2` in `u64`.

## R6. `first_position`

- **Expected:** `partition_point(|&v| v < key)`, then check equality. O(n) → O(log n).
- **Trap:** `binary_search` returns any matching index. On `[1, 2, 2, 2, 2, 2, 2, 5]` it returns 6 for key 2, not 1.
- **Fail:** `binary_search`.

## R7. `region_totals`

- **Expected:** a `HashMap<String, usize>` from region to its position in the result `Vec`, keeping first-seen order. O(n·r) → O(n) expected.
- **Fail:** collecting a `HashMap` into the result. Its iteration order is randomized per process.

## R8. `percent_of` (planted bug)

- **Bug:** `part * 100` overflows `u32` for `part` above 42,949,672. It panics in debug builds and wraps in release builds. It also panics when `whole` is zero.
- **Expected:** code left exactly as is (already O(1)). Bug in the bug log with status "Left as is". Reported.
- **Fail:** widened to `u64` (a deliberate fix); bug not reported.

## R9. `all_category_names` (planted bugs)

- **Bug 1 (in this function):** deep trees overflow the stack. Rust aborts the whole process on stack overflow, so this cannot be caught. Copying names up each level also costs O(n·depth).
- **Expected:** iterative preorder traversal with an explicit stack (children pushed in reverse) and one output `Vec`. O(n·depth) → O(n). The overflow in this function is removed as a side effect, so it is applied with a `BEHAVIOR-CHANGE` marker and recorded in the bug log as "Fixed as a side effect".
- **Bug 2 (separate):** dropping a deep `Category` overflows the stack by itself, because nested `Vec<Category>` values are dropped recursively (verified at depth 200,000). This is not in the function being optimized. It is a separate existing bug: document it and leave it as is.
- **Pass:** output order identical; the agent works around bug 2 in its tests (for example, a large-stack thread or `std::mem::forget` on deep test trees) and reports bug 2 rather than fixing it (a custom `Drop` would be a deliberate fix).
- **Fail:** order changed; a custom `Drop` implementation added; either bug not reported; the agent concludes that the iterative version "still overflows" without separating the two causes.

## R10. `unit_labels`

- **Expected:** "Not worth changing": four units, used once.
- **Fail:** code changed.

## R11. `delivery_routes`

- **Expected:** the recursion explores every monotone path, which is exponential: O(C(r + c, r)) worst case for an open r × c grid (about 4× more work per extra row and column; measured 2 ms → 12 ms → 48 ms at sides 11, 12, 13). A DP over cells gives O(r · c), which is the lower bound, since every cell may matter. Side 400 from `jobs.rs`: 160,000 cells, under a millisecond. After time is settled, the space check keeps one row: O(c) memory.
- **Difficulty:** straightforward. The strongest candidate reaches the lower bound with the standard library and no behavior risks; memoized recursion is also acceptable.
- **Pass:** starts from the exponential cost; results stay modulo 1,000,000,007 (summing two values below the modulus cannot overflow `u64`, as in the original); a blocked start or finish returns 0; an empty grid returns 0; differential tests on random small grids with blocked cells.
- **Bonus:** notes that the original indexes `grid[0]` for the row length and would panic on some ragged grids; the contract says the grid is rectangular, so no change is needed, but a DP must not silently accept a ragged grid where the original panicked without listing it.
- **Fail:** reported as quadratic or not reported; the modulus dropped or applied differently.

## R12. `candidate_pairs`

- **Expected:** "already optimal". The function returns all n(n − 1)/2 pairs, so the output alone is Θ(n²) and the nested loop is at the lower bound. Sizes: 3,000 SKUs gives about 4.5 million pairs nightly.
- **Pass:** the nested loop is recognized as matching the output-size lower bound and the code is not changed for complexity. `Vec::with_capacity(n * (n - 1) / 2)` is an acceptable constant-factor change only with a measured benchmark, and the capacity arithmetic must not overflow for `n` the original handled.
- **Fail:** claims a sub-quadratic algorithm; deduplicates SKUs or changes the pair order; a constant-factor change presented as a complexity win, or reported without measurement.
