# Answer key: ts-shop

Do not copy this file into a run directory. The agent must not see it.

Sizes come from `src/volumes.ts`. Bug planted: T5.

| ID | Location | Rules tested |
|---|---|---|
| T1 | `routing.ts` `shortestHops` | 6 (straightforward), hidden cost of `shift()` |
| T2 | `scheduler.ts` `runOrder` | 6 (reformulate), 7 (no dependency), stability |
| T3 | `indexing.ts` `indexById` | 11 (return type), object key order, `__proto__` key |
| T4 | `filters.ts` `withoutIgnored` | NaN equality trap, 5 |
| T5 | `leaderboard.ts` `rankScores` | 4 (bug in code that cannot be optimized) |
| T6 | `profiles.ts` `loadProfiles` | 5 (behavior change: concurrency and errors) |
| T7 | `permissions.ts` `hasAll` | 32-bit bitmask trap |
| T8 | `reports.ts` `spendReport` | Hidden inputs, cache keys, staleness |
| T9 | `currency.ts` `currencyLabels` | 8 (not worth changing) |
| T10 | `packing.ts` `packsNeeded` | Exponential starting point, 6 (nontrivial), technique assumptions, caching |
| T11 | `restock.ts` `restockList` | Cost along the call chain, object key trap |
| T12 | `invoices.ts` `monthlyStatements` | Cost along the call chain through a callback and a class, first-match duplicates, aliasing |
| TW1 | New `valuation.ts` (write mode, separate run) | Mode selection, workload sizing, cost of existing code called from new code, no silent changes to existing code, per-call cache scope, object key trap |

**Cases with no lift so far.** In round 2 (Opus 5.5, 3 runs per condition), T1, T4, T7, T9, and T11 passed in every run with and without the skill. T7 and T9 are controls (the right answer is to leave the code alone) and T1 is the straightforward control for the compact format; T4 and T11 test traps the model already avoids on its own. Keep them as regression checks, but do not count them as evidence of what the skill adds.

## T1. `shortestHops`

- **Expected:** replace `queue.shift()` with a head index (or a ring buffer). O(V²) worst case → O(V + E).
- **Difficulty:** straightforward.
- **Fail:** an npm queue package without asking; traversal order changed.

## T2. `runOrder`

- **Expected:** all jobs are known up front, so the best approach is to reformulate the problem as a **stable sort** by deadline. `Array.prototype.sort` has been stable since ES2019. O(n²) → O(n log n), with no heap needed. An in-project heap with an index tiebreak is acceptable but is not the best answer.
- **Pass:** ties keep submission order; no dependency added; at least three candidates considered (repeated scan, heap, stable sort).
- **Bonus:** the comparator matches the original `<` semantics for `NaN` and `Infinity` deadlines. `a.deadline - b.deadline` gives `NaN` for `Infinity - Infinity`.
- **Fail:** an npm heap package added without asking; unstable tie order.

## T3. `indexById`

- **Expected:** a single accumulator mutated in a loop, or `Object.fromEntries`. O(n²) → O(n). Keep a plain object.
- **Pass:** return type unchanged; later duplicates still overwrite earlier ones; an id of `"__proto__"` stays an own key. The original's computed key in an object literal creates an own property, `Object.fromEntries` does too, but `index[id] = item` on a plain `{}` sets the prototype instead and drops the item from `Object.keys`.
- **Fail:** assignment into `{}` with no guard for `"__proto__"` (verified to change output); switching to a `Map`. That changes the return type (rule 11) and the iteration order: integer-like keys come first, in ascending order, in plain objects.

## T4. `withoutIgnored`

- **Expected:** a `Set` of ignored values built once. O(r·i) → O(r + i) expected.
- **Trap:** `indexOf` never finds `NaN`, so `NaN` readings are always kept. `Set.has(NaN)` is `true` when `ignored` contains `NaN`, so a plain `Set` would remove them.
- **Pass:** `NaN` behavior preserved (for example, keep a value when `Number.isNaN(value)`), with a `NaN` test. Flagging the difference as a behavior change for review is also a pass.
- **Fail:** a plain `Set` applied silently.

## T5. `rankScores` (planted bug)

- **Bug:** the default `sort()` compares values as strings, so `[3, 10, 2]` becomes `[3, 2, 10]`.
- **Expected:** code left exactly as is. It is already an O(n log n) comparison sort, and the only change would be a deliberate bug fix. Bug in the bug log with status "Left as is". Reported in the conversation.
- **Fail:** a numeric comparator added (a deliberate fix); bug not reported.

## T6. `loadProfiles`

- **Expected:** `Promise.all` or bounded concurrency is a **behavior change**. Today the requests run one at a time, so a failure stops the remaining requests; with `Promise.all`, every request starts and the first rejection wins. Load on the profile service and rate limits also change. Pages are about 50 profiles.
- **Pass:** listed under "Behavior changes for review" and not applied without approval.
- **Fail:** applied silently.

## T7. `hasAll`

- **Expected:** a `Set` of granted permissions built once per call. O(g·r) → O(g + r). Sizes are small (up to 40) but the function is hot (about 3,000 requests per second). "Not worth changing" with stated reasoning is also acceptable.
- **Fail:** a numeric bitmask using `1 << index` for 40 permissions. JavaScript bitwise operators work on 32-bit integers, so permissions past index 30 break. A `BigInt` mask is acceptable but heavy.

## T8. `spendReport`

- **Expected:** no cache keyed only by `(fromDay, toDay)`. `currentUser()` is a hidden input, and `recordEvent` mutates the data.
- **Good answer:** maintain a per-user index (for example, a `Map` from user ID to that user's events, sorted by day with prefix sums) updated in `recordEvent`. The query then costs O(log n) or O(user events) instead of O(all events).
- **Pass:** any cache includes the user and is invalidated by `recordEvent`, or a per-user index is used.
- **Fail:** memoized by date range only; a cache with no invalidation.

## T9. `currencyLabels`

- **Expected:** "Not worth changing": five currencies, called once when a screen opens.
- **Fail:** code changed.

## T10. `packsNeeded`

- **Expected:** the recursion branches once per pack size and recomputes the same remainders, so it is exponential in `units` (about O(k^(units / smallest pack)) worst case for k pack sizes). Replace it with a DP over remainders, either bottom-up or memoized per call: O(units · k) time, O(units) space. Sizes from `volumes.ts`: 2,000 units, 8 pack sizes, so about 16,000 steps. The problem is unbounded change-making, which is NP-hard in general; O(units · k) is pseudo-polynomial and is the best known when `units` is small, which it is here.
- **Difficulty:** nontrivial. Candidates: memoized recursion, bottom-up DP, BFS over remainders, greedy.
- **Pass:** starts from the exponential cost (not reported as quadratic); greedy explicitly **rejected** (`packsNeeded(12, [6, 10])` is 2, while greedy largest-first gives -1); any memo is scoped to one call or keyed by the pack sizes too, because each supplier has its own sizes; `-1` for impossible amounts and `0` for zero units preserved; the lower-bound discussion names the pseudo-polynomial bound.
- **Stack depth:** the original overflows the call stack once `units / smallest pack` passes a few thousand (about 4,660 units with pack size 1 on Node 26). That is above the runbook's 2,000 but still a bug on valid input. A bottom-up DP or BFS removes it as a side effect: that is allowed under rule 4, but must be marked `BEHAVIOR-CHANGE` and recorded in the bug log as fixed as a side effect. A memoized recursion keeps a similar limit, and the exact depth depends on the implementation; it must not overflow on any input the original handles.
- **Bonus:** notices that an array-backed DP throws `RangeError` for negative or fractional `units`, where the original returns `-1`, and either guards those inputs (with integer pack sizes, such totals are unreachable, so `-1` is correct) or lists the difference under behavior changes for review. BFS over remainders with a `Set` handles them without a guard.
- **Fail:** greedy applied; an iterative rewrite that silently stops the stack overflow without documenting it; a module-level memo keyed only by `units` (after `[6, 10]`, a call with `[12]` for 12 units returns 2 instead of 1); not reported at all.

## T11. `restockList`

- **Expected:** `stockOnHand` is O(m) and optimal for a single lookup, but `restockList` calls it for every catalog SKU in every store: O(S · C · M) for S stores, C catalog SKUs, and M movements per store. Sizes: 300 · 8,000 · 25,000 = 6 · 10¹⁰ steps per nightly run. The fix belongs in the caller: aggregate each store's movements into a `Map` from SKU to quantity once, then look up each catalog SKU. O(S · (M + C)) expected. That reaches the lower bound, since the function must read every movement and check every catalog SKU in every store.
- **Difficulty:** straightforward once the cost along the call chain is seen.
- **Pass:** the cost is reported along the call chain, not as "O(m), fine"; `stockOnHand` is left unchanged, since it is exported and optimal on its own; output order (stores in order, catalog order within each store) and duplicate catalog entries are preserved; SKUs that appear in movements but not in the catalog stay excluded.
- **Bonus:** with an empty catalog, store movements are still never read, as in the original (a store with malformed `movements` then does not throw).
- **Fail:** only `stockOnHand` is analyzed, and it is reported as already optimal; a plain object keyed by SKU without guarding prototype keys (a catalog SKU named `constructor` with no movements is dropped instead of reported with 0 on hand); `stockOnHand`'s signature changed.

## T12. `monthlyStatements`

- **Expected:** `PriceBook.priceOf` is a linear `find` over the price list. It runs once per invoice line inside a `reduce` callback in `invoiceTotal`, which `monthlyStatements` calls once per invoice: O(L · P) for L invoice lines and P price entries. Sizes: 150,000 invoices × 12 lines × 250,000 entries ≈ 4.5 · 10¹¹ comparisons. Unlike T11, `monthlyStatements` cannot index the prices itself, because `entries` is private. Two fixes reach O(L + P) expected, which is the lower bound:
  - **Persistent index:** a `Map` from SKU to its **first** entry inside `PriceBook`, maintained in `add` (or built lazily and invalidated by `add`). It can go stale (see "Behavior risks"), so it is a behavior change for review.
  - **Per-call index:** a new `PriceBook` method that builds a SKU-to-first-entry lookup from the current entries, called once at the start of each `monthlyStatements` run and discarded at the end. Nothing can change the price book during one synchronous run, so this matches the original on every input and needs no approval. Adding a method does not change any existing signature, so it keeps the public contract (rule 11), but the report must name the new method. With the persistent index declined, this is the expected answer. Proposing the persistent index for review first and then applying the per-call index is also a pass.
- **Difficulty:** nontrivial. Candidates: an index maintained in `add`; a lazy index invalidated on `add`; sorting entries plus binary search; a per-call index built through a new `PriceBook` method.
- **Pass:** the cost is reported along the whole chain (`monthlyStatements` → `invoiceTotal` → `priceOf`); the first listing still wins for duplicate SKUs; `priceOf`'s signature and the summation order are unchanged. A persistent index stores the entry object (or reads `cents` at lookup time), because callers keep references to the entries they pass to `add`, and the original sees later changes to `cents`. A per-call index may store `cents`, since it is rebuilt on every run.
- **Behavior risks the agent must name (persistent index):** a caller changing an entry's `sku` after `add` makes a persistent SKU index stale. Tests cannot rule that out, so it goes under behavior changes for review or is called out as unverified. A per-call index does not have this risk.
- **Fail:** `new Map(entries.map(...))` or `set` on every `add`, so the **last** listing wins (verified: a duplicate SKU listed at 100 then 999 returns 999 instead of 100); a persistent index that stores `cents` values, so later changes to an entry are missed (verified: the original returns 150 after the change, the snapshot returns 100); a persistent index applied on "apply all" without item-by-item approval; a per-call index cached beyond one run; only `invoiceTotal` or only `priceOf` analyzed in isolation.

## TW1. `stockValuation` (write mode)

Run this case in its own fresh run directory, not after the report and apply prompts. Prompt:

```
Add a function stockValuation(stores, priceBook) in a new file src/valuation.ts. For each store, in the order given, it returns the store id and the total value in cents of the stock on hand: for every SKU with a positive net quantity in that store's movements, quantity times the SKU's price from the price book. Add tests.
```

- **Expected mode:** write mode, stated in the first reply. No mode question is needed: the request is plainly new code.
- **Sizes** (from `volumes.ts`): S = 300 stores, M = 25,000 movements per store, D ≤ about 8,000 distinct SKUs (the catalog size), P = 250,000 price-book entries.
- **Expected:**
  - Net quantities per store aggregated in one pass into a `Map` from SKU to quantity: O(M) per store. Not `stockOnHand` called once per SKU, which is O(D · M) per store: 300 · 8,000 · 25,000 = 6 · 10¹⁰ steps.
  - `PriceBook.priceOf` is a linear `find` (O(P)), and `entries` is private, so new code cannot index it. Each distinct SKU is priced at most once per `stockValuation` call, through a `Map` created inside the call: at most D · P = 2 · 10⁹ comparisons, instead of 300 · 8,000 · 250,000 = 6 · 10¹¹ when every store prices every SKU again, or more when pricing per movement.
  - `PriceBook` and `inventory.ts` are left unchanged. The summary reports `priceOf` as the remaining bottleneck, cost along the call chain included, recommends indexing inside `PriceBook` (the T12 fix, keeping first-listing-wins), and asks whether to apply it.
  - Total: O(S · M + D · P) expected with the existing `PriceBook`; O(S · M + P) once the `PriceBook` index is approved.
- **Pass:** all of the above; output in store order; SKUs with zero or negative net quantity excluded; a "Performance decisions" list with size assumptions and complexities; tests include a case at realistic size that runs in reasonable time, with no timing assertion.
- **Bonus:** the price cache stores the price, which is safe within one synchronous call (nothing can call `add` or change an entry in between), and the summary says why.
- **Fail:**
  - `stockOnHand` called once per SKU per store.
  - `priceOf` called once per SKU per store, or once per movement.
  - `PriceBook` changed (an index added, `entries` made public) without asking.
  - A module-level price cache that outlives the call: later `add` calls or changed entries are then missed.
  - Quantities kept in a plain object without guarding prototype keys (a SKU named `constructor` reads `Object.prototype.constructor` as its starting quantity), as in T11.
  - An optimization report produced instead of the feature; a dependency added; parallelism or workers introduced.

