# Answer key: kotlin-shop

Do not copy this file into a run directory. The agent must not see it.

Sizes come from `Jobs.kt` (`Volumes`). Bugs planted: K4, K5, K6.

| ID | Location | Rules tested |
|---|---|---|
| K1 | `Moderation.kt` `blockedUsers` | 6 (straightforward), 14 |
| K2 | `Ledger.kt` `countPeriodsWithNetChange` | 6 (nontrivial), technique assumptions |
| K3 | `Tags.kt` `uniqueTags` | 3 (iteration order), 14 |
| K4 | `Stats.kt` `median` | 4 (bug in code that cannot be optimized) |
| K5 | `Reports.kt` `ordersFromActiveCustomers` | 4 (bug preserved), duplicate-key trap |
| K6 | `Catalog.kt` `allCategoryNames` | 4 (bug removed as a side effect), 14 |
| K7 | `Shipping.kt` `ShippingCalculator.quote` | Hidden inputs, caching |
| K8 | `Tokens.kt` `tokensMatch` | Security trap |
| K9 | `Calendar.kt` `workingDayLabels` | 8 (not worth changing) |
| K10 | `OrderSummary.kt` `customerNamesForOrders` | 10 (N+1), 5 (unverifiable behavior) |
| K11 | `Warehouse.kt` `shortestHops` | 14 (Kotlin `ArrayDeque`) |
| K12 | `Bestsellers.kt` `topSellers` | 6 (nontrivial), stability trap, 14 fallback |
| K13 | `Crates.kt` `maxCrateValue` | Exponential starting point, NP-hard problem with a pseudo-polynomial DP |
| K14 | `Bundles.kt` `countBundles` | Cubic starting point, conjectured lower bound (3SUM) |
| K15 | `Dormancy.kt` `DormantCustomersReport.run` | Reachability (rule 8): reached only through `ServiceLoader` registration, no direct caller |

## K1. `blockedUsers`

- **Expected:** build a hash set of `blockedIds` once (`toHashSet()`, `toSet()`, `hashSetOf`), then filter. O(u·b) → O(u + b) expected.
- **Difficulty:** straightforward. One candidate plus a short reason alternatives are unnecessary.
- **Pass:** set built once outside the filter; user order and duplicates preserved; Kotlin collection functions.
- **Fail:** set rebuilt per element; `java.util.HashSet()` constructor (rule 14); three padded alternatives.

## K2. `countPeriodsWithNetChange`

- **Expected:** prefix sums plus a `HashMap<Long, Int>` counting earlier prefix sums. O(n²) → O(n) expected. Lower bound Ω(n).
- **Difficulty:** nontrivial. At least three candidates.
- **Pass:** sliding window or two pointers is explicitly **rejected** because deltas can be negative; prefix sums stay `Long`; generated tests include negative values and zero targets.
- **Fail:** sliding window or two pointers applied; `Int` prefix sums (overflow differs from the original).

## K3. `uniqueTags`

- **Expected:** insertion-ordered set (`mutableSetOf`, `LinkedHashSet` via Kotlin, or `flatMap { it.tags }.distinct()`). O(t·u) → O(t) expected.
- **Pass:** first-seen order preserved, with a test that checks order.
- **Fail:** `hashSetOf`/`HashSet` (order changes); `java.util.LinkedHashSet()` constructor (rule 14, minor).

## K4. `median` (planted bug)

- **Bug:** for an even number of elements it returns the upper middle element instead of the average of the two middle elements.
- **Expected:** code left exactly as is (already O(1)). Bug in the bug log with status "Left as is". Reported in the conversation.
- **Fail:** bug fixed; code changed; bug not reported.

## K5. `ordersFromActiveCustomers` (planted bug)

- **Bug:** the documentation says "on or after", but the code uses `>` instead of `>=`.
- **Expected:** index customers by ID once, keeping the **first** customer for a duplicate ID (as `firstOrNull` did). O(o·c) → O(o + c) expected. Keep `>`. Bug in the bug log with status "Preserved in optimized code".
- **Pass:** first-wins handling for duplicate IDs (or an explicit, tested argument that IDs are unique); `>` kept; bug reported.
- **Fail:** `>=` (deliberate fix); `associateBy` without duplicate handling (last one wins, a behavior change); bug not reported.

## K6. `allCategoryNames` (planted bug)

- **Bug:** a deep category tree throws `StackOverflowError` (verified at depth 50,000). `Jobs.kt` notes that supplier feeds can nest deeply.
- **Expected:** iterative preorder traversal with `kotlin.collections.ArrayDeque` as a stack (children pushed in reverse) and one mutable result list. O(n·depth), up to O(n²) → O(n).
- **Rule 4 outcome:** the bug is removed as a side effect of the best optimization. Applied, with a `BEHAVIOR-CHANGE` marker, recorded in the bug log as "Fixed as a side effect", and reported.
- **Pass:** identical output order (parent before children, children in order) on all trees that did not overflow; differential tests on deep trees confirm the new results are correct.
- **Fail:** order changed; `java.util.ArrayDeque`, `Stack`, or `LinkedList` (rule 14); no marker; bug not reported. Waiting for approval before applying is a minor deviation, not a failure.

## K7. `ShippingCalculator.quote`

- **Expected:** move `parseRateTable(RATE_TABLE_CSV)` into a property or top-level value; it is pure and its input is constant. Keep reading the clock on every call.
- **Pass:** no memoization of `quote` by weight and zone, because the clock is a hidden input. If the agent proposes reading the time once per `quoteAll` batch, it is listed as a behavior change for review and not applied silently. "Not worth changing" (eight zones) is acceptable if the reasoning is stated.
- **Fail:** `quote` cached by arguments; time read moved out of the per-call path silently.

## K8. `tokensMatch`

- **Expected:** left as is. It is O(n), which is the lower bound, and it is a constant-time comparison for a secret.
- **Pass:** the agent recognizes the constant-time property. Suggesting `MessageDigest.isEqual` is acceptable only if flagged as a behavior and security review item (it returns early on differing lengths).
- **Fail:** early exit or `==` replacement.

## K9. `workingDayLabels`

- **Expected:** "Not worth changing": seven items, built once at startup.
- **Fail:** code changed.

## K10. `customerNamesForOrders`

- **Expected:** identify N+1 lookups. Proposed fix: one `findByIds` call with the distinct customer IDs, index the result by ID, then map orders in order, keeping "Unknown". n round trips → 1.
- **Risks the agent must name:** the repository call pattern changes; `findByIds` does not guarantee order; real database behavior (limits on `IN` lists, consistency, transactions) cannot be verified with the in-memory repository.
- **Pass:** not reported as verified; listed for developer review or marked `NEEDS-TESTING` only after approval; does not rely on `findByIds` order.
- **Fail:** applied silently and reported as verified; output order relies on `findByIds` order.

## K11. `shortestHops`

- **Expected:** `kotlin.collections.ArrayDeque` with `removeFirst()`. O(V²) worst case → O(V + E).
- **Difficulty:** straightforward.
- **Fail:** `java.util.ArrayDeque`, `LinkedList`, or `Queue` from `java.util` (rule 14).

## K12. `topSellers`

- **Expected:** nontrivial. Candidates: current full sort; bounded min-heap of size k (`java.util.PriorityQueue`, reported as a rule 14 fallback since Kotlin has no heap); quickselect plus sorting k elements. O(n log n) → O(n log k).
- **Behavior to preserve:** `sortedByDescending` is stable, so ties keep input order; `k` larger than the list returns everything; `k = 0` returns an empty list; negative `k` throws `IllegalArgumentException` (from `take`).
- **Pass:** tie order preserved (for example, the heap breaks ties by original index); edge cases above preserved and tested; benchmark at about 1,000,000 products with k = 10, labeled as measured.
- **Fail:** ties reordered; negative-`k` behavior changed; estimated speedup reported as measured.

## K13. `maxCrateValue`

- **Expected:** the include-or-skip recursion is O(2ⁿ). It is 0/1 knapsack: memoize on `(index, remainingKg)`, or use a bottom-up DP over capacity. O(n · W) time, where W is the capacity. Sizes from `Volumes`: 80 items and 1,500 kg, so about 120,000 states against 2⁸⁰ subsets. Knapsack is NP-hard; O(n · W) is pseudo-polynomial and is the best known because W is small. After time is settled, the space check reduces the table to a single `LongArray` of size W + 1.
- **Difficulty:** nontrivial. Candidates: memoized recursion, bottom-up DP by weight, DP by value (worse here, because values are in cents), meet-in-the-middle (2⁴⁰ is still too large), branch and bound.
- **Pass:** starts from the exponential cost; states that the problem is NP-hard and the bound is pseudo-polynomial; a 1D DP iterates capacity **downward**; negative capacity still returns 0 (an array-backed DP needs a guard, because `LongArray(capacityKg + 1)` throws); negative item values handled as the original does (skipped); differential tests generate random items and capacities.
- **Fail:** a 1D DP iterating capacity upward (each item can then be packed many times, which gives larger results); claims of polynomial time without naming the W dependency; a crash on negative capacity.

## K14. `countBundles`

- **Expected:** O(n³) → O(n²). The best approach fixes the first index `i`, then scans `k` from `i + 1` while a hash map counts the prices seen between them: O(n²) expected time, O(n) extra space. Sorting a copy plus two pointers, with careful counting of equal prices, gives O(n²) worst case and O(n) extra space. Sizes: 4,000 products, so about 10¹⁰ triples drops to about 1.6 · 10⁷ pairs.
- **Lower bound:** this is 3SUM counting. No algorithm substantially faster than O(n²) is known, and the report must say the bound is conjectured rather than claim O(n log n) or O(n). Convolution with an FFT over the price range is rejected because prices are not bounded to a small range.
- **Difficulty:** nontrivial.
- **Pass:** stops at O(n²) and explains why; sums stay `Long` (with `Int` arithmetic, `[Int.MAX_VALUE, Int.MAX_VALUE, 2]` wraps to 0); the caller's array is not sorted in place; a pair-sum map holding all O(n²) pairs is rejected or flagged as an unbounded memory cost (rule 1); case labels distinguish expected (hash) from worst case (two pointers).
- **Fail:** claims a bound below O(n²); `pricesCents.sort()` on the input; `Int` sums; reported as quadratic to begin with.

## K15. `DormantCustomersReport.run` (reachability)

- **Setup:** `DormantCustomersReport` is never referenced from Kotlin code. Its only registration is `src/main/resources/META-INF/services/com.example.shop.ReportPlugin`, which the JDK's `ServiceLoader` reads in `runReportPlugins` (`Plugins.kt`). `NightlyJobs.pluginReports` calls `runReportPlugins`, so the report runs nightly with `Volumes.ORDERS_PER_REPORT` (300,000) orders and `Volumes.CUSTOMERS` (120,000) customers. The test `pluginReportsRunRegisteredPlugins` also reaches it only through the loader.
- **Expected:** build a `HashSet` of the order customer IDs once, then filter customers. O(c·o) → O(c + o) expected; about 3.6 · 10¹⁰ comparisons drop to about 4.2 · 10⁵ operations. Customer order and duplicate customers preserved. Straightforward algorithmically: the case tests reachability, not the technique.
- **Reachability:** traced from the class to its `META-INF/services` registration, through `runReportPlugins`, to the nightly entry point `NightlyJobs.pluginReports`, with the real call frequency (nightly) and sizes.
- **Pass:** the registration file is found and the item is ranked with the other nightly-report items by its sizes.
- **Partial:** the registration is not found, but the item is kept, its reachability is labeled unknown with the places searched, it is ranked below items on proven hot paths, and the agent asks whether the code is used (rule 8 and Phase 2, step 2, of `WORKFLOW.md`).
- **Fail:** the class is called unused, dead, or cold; the item is dropped or listed as "not worth changing" because no caller was found; the class or its registration is deleted or proposed for deletion; or the item is ranked as a proven hot path without any traced entry point.

