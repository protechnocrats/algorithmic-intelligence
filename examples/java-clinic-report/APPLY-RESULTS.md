# Apply results

Items refer to IDs in `OPTIMIZATION-REPORT.md`. Developer request: "apply all the optimizations you recommend." Under rule 5, that covers only items whose equivalence is verified. The items with known behavior changes (OPT-5 / BC-1, OPT-7 / BC-2) and BC-3 are **not applied**; a later instruction declined every approval request, so they stay unapplied. Nothing is committed (commits were not authorized); the per-item file lists below are how to review or revert each item.

## Test suite

- **Before:** 12 passed, 0 failed.
- **After (final code):** 26 passed, 0 failed. The 12 existing tests plus 14 new differential tests in `src/test/java/com/example/clinic/OptimizationEquivalenceTest.java`.

## Applied items

### OPT-1. Repeated-visit check: sort-based, O(n log n) worst case. Applied (verified: exhaustively checked to a stated bound + property-checked)

- **Verification:** Exhaustive over every upload of length 0–6 drawn from {null, 3 keys} (5,461 cases, nulls included). Random uploads up to 4,000 rows with 1–30 distinct keys (200 cases). Results and exception types compared with the original.
- **Null elements:** kept exactly. Any upload containing a null is passed to the verbatim original routine, so which calls throw NPE is unchanged. This resolves BC-4 without a behavior change.
- **Performance (measured):** n = 16,000 distinct: 438 ms before → 8.6 ms after. n = 200,000 distinct (the upload limit): estimate was about 68 s; measured 21–60 ms.
- **Reproduce:** `bash test.sh`; scratch benchmark in `/tmp/cxo/bench` (not in the project).
- **Changed files:** `PartnerImport.java`, function `repeatedVisits` (new sort-based path; old code kept as `repeatedVisitsWithNulls`).

### OPT-2. `minutesUntilOpen`: precomputed wait table, O(1) per query. Applied (verified: exhaustively checked for the given calendars)

- **Verification:** For `outpatients()`, all 10,080 minutes compared. For 40 random calendars (0–5 sessions, including wrap-around and single-minute sessions), all 10,080 minutes each. Empty calendar and out-of-range minutes (both exception types) compared.
- **Performance (measured):** average per call 0.0029 ms → 0.0001 ms (includes table lookup and loop overhead of the benchmark). Night estimate at 40M calls: 117 s → about 3 s in this harness, with the single-thread caveat from the benchmark.
- **Cost of the change:** the table is built in the constructor: 40,320 bytes per `SessionCalendar` instance, and about 100,000 operations per construction. `outpatients()` still builds a new instance on each call, so a caller that invokes it per request pays that build each time. Not measured; estimated at tens of microseconds.
- **Changed files:** `SessionCalendar.java`, `minutesUntilOpen` and the constructor (new `buildWaitTable`); `isOpen` removed.

### OPT-3. Label lookup: hash index plus precompiled pattern. Applied (verified: exhaustively checked to a stated bound)

- **Verification:** Exhaustive over all raw strings of length 0–5 over the 7 characters `LA 2-:7`, for a duplicate-code terminology (first match wins), and for a terminology containing a null code (the original scan is used in that case, so the NPE behavior is identical). Reload visibility is tested with a before/after terminology. Random terminologies tested with raw strings of length ≤ 3.
- **Caught bug:** the first version of the duplicate test used codes the alphabet could never produce, so the planted bug survived. The test was fixed (codes now drawn from the alphabet), and the planted bug is now caught.
- **Performance (measured):** matched code at the end of the 90,000-term list: 609 ms → 23.8 ms for 2,000 calls (about 25×, about 12 µs per call; the original was 0.30 ms per call). Free text: 128 ms → 101 ms for 200,000 calls (the pattern is no longer compiled per call; the gain is smaller than the estimate).
- **Memory:** one `HashMap` of up to 90,000 entries per `CodeFormatter` (not measured). Intended to be shared, one per process.
- **Changed files:** `CodeFormatter.java`: static pattern, `Snapshot` (list + index, published with one volatile write), `label`, `reload`.

### OPT-4. `roomsNeeded`: interval sweep, O(n log n). Applied (verified: exhaustively checked to a stated bound, plus randomized comparison)

- **Verification:** Exhaustive over every ordered list of up to 4 half-open intervals with endpoints in [0, 4] (11,111 cases). Random lists up to 12 appointments (1,500 cases) compared against the original exact search. An invalid appointment throws the same exception. Scratch check from the analysis (3,000 random instances, n ≤ 12) also passes.
- **Performance (measured):** n = 30: 9.5 s → 0.2 ms. n = 400: unbounded before (no completion) → 1.6 ms.
- **Changed files:** `RoomPlanner.java`, `roomsNeeded`.

### OPT-6. Ledger totals: one pass per distinct start, bit-identical. Applied (verified: exhaustively checked to a stated bound, bit-for-bit)

- **Verification:** Totals compared with `Double.doubleToRawLongBits`, so signed zeros and NaN are included. Exhaustive over all arrays of length 3 with values {+0.0, −0.0, 0.1}, and all lists of up to 2 ranges with endpoints in [−1, 4] (including invalid ones). Random arrays up to 200,000 entries with special values (NaN, ±∞, ±0.0, subnormal, large magnitudes), up to 300 ranges with 1–24 distinct starts, and empty ranges.
- **Performance:** measured 200 ranges, 1M entries: 43.7 ms → 10.3 ms (one run each, warm-up included; the advantage depends on the mix of ranges). The worst case with all distinct starts is unchanged (documented in the report).
- **Changed files:** `Ledger.java`, `rangeTotals`.

### OPT-8. `weeklyRoomsNeeded`: exact branch and bound (clique lower bound, DSATUR ordering, DSATUR upper bound, symmetry breaking). Applied (verified: tested; exhaustive for small cases only through the random differential checks)

- **Verification:** 1,200 random instances (0–8 slots; starts biased to the week boundaries; lengths from 1 to a full week), plus 150 dense instances with 9–12 slots of 1,000–4,000 minutes, all compared with the original exact search. The invalid-slot exception is compared too. Planted bugs in the new search (a wrong returned count; forbidding new colours) were both caught.
- **Process:** the first version was the pruned search (clique lower bound and symmetry breaking only). On dense instances it still timed out at n ≥ 40, so the branch-and-bound step the report named as the next candidate was added. Only the final version is kept.
- **Performance (measured, final version):**
  - Dense (length 1,500–4,000 minutes, the same instances for all versions): original times out on every instance from n = 20. Final: n = 20 in 0.4–1.5 ms, n = 30 in 0.5–1.0 ms, n = 40 in 0.9 ms, 1.5 ms and 678 ms, n = 60 in 1.9–2.2 ms.
  - Sparse (length 30–630 minutes): original times out at n = 40 (n = 20 takes 2.4 s). Final: n = 60 in 4.1 ms.
- **Status of the remaining cost:** still exponential in the worst case (the problem is NP-hard; see OPT-8 in the report). The 678 ms dense n = 40 instance shows a hard case still exists. No worst-case bound was established, and the results match the original wherever the original finishes.
- **Changed files:** `RoomPlanner.java`, `weeklyRoomsNeeded`, `cliqueLowerBound`, `fewestRooms`, `colourDsatur`, `search`, `colourCount`. The earlier `assign` helper was removed.

### OPT-9. `notStocked`: hash set lookup. Applied (verified: exhaustively checked to a stated bound)

- **Verification:** Exhaustive over all order lists and stock lists of length 0–3 over {"A", "B", null, ""}, including null stock lists (exception type compared). Large random lists (20,000 items, 30,000 stock, duplicates, one stocked null).
- **Known difference (not a behavior change for callers):** when the stock list is null and the order is non-empty, both versions throw `NullPointerException`, but the message differs (the set is built from the null list instead of calling `contains` on it). Exception type is the same.
- **Performance (measured):** 20,000 × 30,000, no matches: 985 ms → 11.4 ms.
- **Changed files:** `Supplies.java`, `notStocked`.

## Not applied

Declined by the developer's instruction ("decline every approval request"). Each needs explicit approval, and none was applied.

- **OPT-5 / BC-1 (reminder batching):** declined. Known behavior change (provider call pattern; per-message decisions unverified).
- **OPT-7 / BC-2 (roster batch lookup):** declined. Known behavior change (call pattern and failure timing).
- **BC-3 (prefix sums in ledger):** declined; not recommended anyway. Known behavior change.

No dependency was requested, so none was added.
- **OPT-10 (`Availability`):** caller advice, no change in this repository.
- **Not worth changing (unchanged):** `ChartViewer` / `ChartRepository`, `RosterService.clock`.

## Needs testing / behavior changes decided

- None applied with a known behavior change, so no `NEEDS-TESTING` or `BEHAVIOR-CHANGE` markers were added.

## Tried and rejected while applying

- **OPT-8, pruned search without DSATUR** (first version, clique lower bound plus symmetry breaking): kept only as an intermediate step. Measured: dense n ≥ 40 still timed out. Superseded by the final branch and bound.

## Bugs found while applying

- No new bugs. BUG-1 (null elements in `repeatedVisits`) is unchanged: the optimized code keeps the original routine for uploads that contain a null.

## Changed files (per item)

- OPT-1: `PartnerImport.java`
- OPT-2: `SessionCalendar.java`
- OPT-3: `CodeFormatter.java`
- OPT-4: `RoomPlanner.java` (`roomsNeeded`)
- OPT-6: `Ledger.java`
- OPT-8: `RoomPlanner.java` (`weeklyRoomsNeeded` and its helpers)
- OPT-9: `Supplies.java`
- Tests (new): `src/test/java/com/example/clinic/OptimizationEquivalenceTest.java`

## Planted-bug check ("check the check")

Nine deliberate bugs were planted one at a time in scratch copies (not in the project). Each was caught by the new tests. The last two were added for the final weekly search:

| Planted bug | Caught by |
|---|---|
| Sweep end boundary off by one (`<` instead of `<=`) | `roomsNeededRandomLarger` |
| Weekly clique bound one too high | `weeklyRoomsNeededMatchesOriginal` |
| Ledger pass starts one position late | `ledgerRandomLarge` |
| Duplicate sort ignores patient id | `partnerImportRandomLarge` |
| Wait table off by one | `minutesUntilOpenRandomCalendars` |
| Label index keeps the last duplicate | `codeFormatterExhaustiveRawCodes` (after the test fix described under OPT-3) |
| Supplies check inverted | `notStockedRandomLarge` |
| Branch-and-bound returns k + 1 | `weeklyRoomsNeededMatchesOriginal` |
| Branch-and-bound forbids opening new colours | `weeklyRoomsNeededMatchesOriginal` |

The unmodified code passes all 14 new tests.

## Reproduce

- `bash test.sh` (compiles, runs all 26 tests). Requires a JDK with `javac` on PATH.
- Benchmarks were run from scratch programs in `/tmp/cxo/bench` (not in the project; not committed).

## Commits

Not made. Commits were not authorized in this conversation or the project instructions. Changed files are listed per item above.
