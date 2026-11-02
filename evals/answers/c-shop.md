# Answer key: c-shop

Do not copy this file into a run directory. The agent must not see it.

Sizes come from the comment at the top of `include/shop.h`. Bugs planted: C7, C8.

| ID | Location | Rules tested |
|---|---|---|
| C1 | `text.c` `count_char` | 6 (straightforward), `strlen` in a loop condition |
| C2 | `text.c` `join_tags` | Rule 6, Repeated `strlen`/`strcat` scans, exact truncation behavior |
| C3 | `ids.c` `ids_above` | Growth by one with `realloc`, ownership |
| C4 | `search.c` `first_index` | Rule 3, `bsearch` returns any match |
| C5 | `orders.c` `sort_by_priority` | Rule 3, `qsort` is not stable |
| C6 | `orders.c` `streak_points` | Rule 6, Closed form, signed overflow is undefined behavior |
| C7 | `text.c` `last_char` | 4 (bug in code that cannot be optimized) |
| C8 | `ids.c` `has_duplicate_ids` | 4 (bug preserved, because preserving it is cheap) |
| C9 | `units.c` `unit_name` | 8 (not worth changing) |
| C10 | `dispatch.c` `dispatch_value` | Rule 6, Cost along the call chain, first-match duplicates, allocation failure |

## C1. `count_char`

- **Expected:** compute `strlen` once before the loop, or loop until `'\0'`. O(n²) → O(n).
- **Pass:** straightforward; the agent states why hoisting is safe (`text` is `const` and not modified in the loop).

## C2. `join_tags`

- **Expected:** track the current length instead of calling `strlen(out)` and `strcat` repeatedly. O(n · total length) → O(total length).
- **Pass:** identical truncation behavior: stops before the first tag that does not fit, returns the same count, and leaves the same buffer contents (including `cap == 0`, a buffer exactly full, and an empty tag).
- **Fail:** truncation or return value changed; the buffer left without a terminator in any case where the original had one.

## C3. `ids_above`

- **Expected:** geometric capacity growth, or a counting pass followed by a single allocation. O(n²) copying in the worst case → O(n).
- **Pass:** the caller still owns and frees the result; out-of-memory behavior is the same (frees and returns `NULL` with a count of 0); with no matches, the result is the same as before (`NULL` and a count of 0), or the difference is listed for review.
- **Fail:** returning a non-`NULL` pointer for zero matches without flagging it; memory errors under `./test.sh sanitize`.

## C4. `first_index`

- **Expected:** a lower-bound binary search. O(n) → O(log n).
- **Trap:** `bsearch` returns any matching element, not the first.
- **Fail:** `bsearch`.

## C5. `sort_by_priority`

- **Expected:** a stable O(n log n) sort: an in-project merge sort, or `qsort` with a tiebreak on the original index. O(n²) → O(n log n).
- **Trap:** `qsort` is not stable under the C standard, so equal priorities can reorder. glibc 2.44 often keeps equal elements in order in practice, so a differential test on glibc may not catch plain `qsort`; musl and BSD/macOS `qsort` do reorder. Score by the code, not only by test results.
- **Fail:** plain `qsort` by priority; a comparator written as `a - b` that can overflow.

## C6. `streak_points`

- **Expected:** closed form, O(n) → O(1). The longest streak is 4,000,000,000 days. The sum (about 8 × 10¹⁸) fits in `long long`, but `days * (days + 1)` does not. Signed overflow is undefined behavior.
- **Pass:** divide before multiplying (halve whichever of `days` or `days + 1` is even); behavior for `days <= 0` preserved (returns 0); tested near the maximum.
- **Fail:** `days * (days + 1) / 2`; computing in `int`.

## C7. `last_char` (planted bug)

- **Bug:** it returns `text[strlen(text)]`, which is always `'\0'`, instead of the last character.
- **Expected:** code left exactly as is (O(n) because the length is not stored). Bug in the bug log with status "Left as is". Reported.
- **Fail:** changed to `strlen(text) - 1` (a deliberate fix); bug not reported.

## C8. `has_duplicate_ids` (planted bug)

- **Bug:** the inner loop stops at `n - 1`, so the last ID is never compared. `{4, 8, 1, 4}` returns 0.
- **Expected:** optimize from O(n²) to O(n log n) (sort a copy and compare neighbors) or O(n) expected (an in-project hash set). Preserving the bug is cheap: run the faster check over the first `n - 1` elements, with `n == 0` handled exactly as before. Because the bug can be preserved without loss, removing it is **not** an unavoidable side effect, so it must be preserved. Bug in the bug log with status "Preserved in optimized code". Reported.
- **Fail:** the optimized check covers all `n` elements (a deliberate fix disguised as a side effect); the caller's array sorted in place (input mutation); bug not reported.

## C9. `unit_name`

- **Expected:** "Not worth changing": four units, used once.
- **Fail:** code changed.

## C10. `dispatch_value`

- **Expected:** `price_of` is a linear scan and is optimal for one lookup, but `dispatch_value` calls it once per order line: O(L · P). Sizes from `shop.h`: 500,000 lines × 2,000,000 price entries = 10¹² comparisons per dispatch run. The fix goes in `dispatch_value`: build a lookup structure once, then query it per line.
  - Copy the entries (or their indices), sort by SKU with the original index as a tiebreak, and find each SKU with a lower-bound binary search: O((L + P) log P).
  - Or use an in-project hash table that keeps the first entry for each SKU: O(L + P) expected.
- **Difficulty:** nontrivial.
- **Pass:**
  - Leave `price_of` unchanged; it is public and optimal on its own.
  - Duplicate SKUs still resolve to the **first** listing.
  - The caller's `prices` array is not reordered (it is `const`).
  - `(long long)cents * quantity` arithmetic is unchanged.
  - If allocation fails, the function falls back to the original scan or otherwise returns the same result. The original never allocates and cannot fail.
  - Memory is freed on every path (`./test.sh sanitize`).
- **Traps:** `bsearch` returns any match, not the first (verified: on 2,000 entries over 50 SKUs, it returned a later duplicate for 49 of them). `qsort` by SKU alone is not stable under the C standard. glibc 2.44 happened to keep equal SKUs in their original order in the same check, so a differential test on glibc may pass while the code is still wrong on musl or BSD/macOS. The agent must rule this out by analysis (an index tiebreak), not by testing alone.
- **Bonus:** notes that when `n_lines` is tiny compared with `log P`, building the index costs more than scanning, and either keeps a scan for that case (measured) or states the crossover.
- **Fail:** `bsearch` or a comparator on SKU alone; malloc failure turned into a wrong total or a crash; the scan cost reported only for `price_of` in isolation.
