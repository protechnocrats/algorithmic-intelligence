# Answer key: py-logistics (held out)

Do not copy this file into a run directory. The agent must not see it.

**Held-out fixture.** Use it only to measure the skill, never to tune its wording. If a result here leads to a change in the skill, the change must be checked on the tuned fixtures, and this fixture stops being held out for the next round: build a new one.

Python with the standard library only. Rounds 1 to 3 ran before `languages/PYTHON.md` existed and so tested `languages/GENERIC.md`; later runs load `PYTHON.md`, which states CPython's integer hashing (P5) and negative-index wraparound (P3) as general facts, so P3 and P5 results are not comparable across that change. Sizes come from `logistics/volumes.py`. Tests: `./test.sh`. Grading probe: `evals/probes/py-logistics.py`.

Each case targets one role from the project's vision, plus hostile input and a straightforward control.

| ID | Location | Role | Rules and files tested |
|---|---|---|---|
| P1 | `profit.py` `best_operating_plan` | Algorithms researcher | Rule 6, `DISCOVERY.md` (a custom rule no table names), contract preservation, provenance label, verification level for a derived algorithm |
| P2 | `quotes.py` `QuoteBook` | Performance engineer | Profiling, bottleneck classification (a lock held across network I/O, not the loop), rule 5 for a concurrency change |
| P3 | `business_days.py` `business_days_between` | Formal-methods engineer | Contract written first, verification levels 3 and 4 on a finite domain, error contract |
| P4 | `depots.py` `nearest_depot` | Experimental scientist | Prediction before measurement, "tried and rejected," rule 8 at small n on a hot path |
| P5 | `bulk.py` `repeated_ids` | Hostile input | Rule 9, Exposure check, `techniques/hostile-inputs.md`, CPython integer hashing |
| P6 | `manifest.py` `unmatched_parcels` | Control (straightforward) | Rule 6, Compact report format, order and repeats kept |
| PW1 | New `sla.py` (write mode, separate run) | Write mode | Rule 3, Reference version in the tests, contract checks, verification level, sliding-window assumptions |

## P1. `best_operating_plan` (researcher)

**Replaced on 2026-10-31,** after round 3. The earlier P1 (maximum run with one day dropped) is a known exercise ("maximum subarray with one deletion"), so models solved it from memory and never needed `DISCOVERY.md`. The new P1 is a custom business rule with no textbook name. No run had seen it when it was added.

- **Problem:** the most profitable run of consecutive days when the depot may close on up to k days inside the run. A closed day earns −`closure_cost` instead of its profit; no two closed days may be adjacent; the first and last days of the run stay open. The original enumerates every run and every allowed set of closures: about n² · C(n, k) · n. Measured: 0.03 s at 20 days and 0.67 s at 40 days with k = 3, about 22 times per doubling. At 3,650 days a night it never finishes.
- **Expected derivation:** carry the best run forward (move 2) and design the state from the invariant (move 3). For each day and each number of closures used c ≤ k, keep the best run ending today with today open, and with today closed:
  `open[c] = profit + max(open_prev[c], closed_prev[c], 0 if c == 0)`, `closed[c] = open_prev[c − 1] − closure_cost`, answer `max(open[c])` over all days and c. O(n · k) time, O(k) space; the lower bound is Ω(n).
- **Contract traps** (each checked by the probe on random inputs):
  - The run's first and last days stay open. With a negative `closure_cost` (closing earns money), a solution that may close an end day returns more than the original.
  - No two closures are adjacent. A solution that ignores this returns more than the original when bad days come in pairs.
  - All-negative input with k = 0 returns the largest single day, not 0.
  - An empty list and a negative `max_closures` raise `ValueError`.
- **Pass:** O(n · k) applied with matching outputs; provenance labeled *derived*, with the invariant (the states and what each holds) written down; verification level 2 or higher, ideally an exhaustive check of all short lists over small values and every k ≤ 3; the discovery moves used named.
- **Fail:** any probe difference (an end day closed, adjacent closures, 0 for all-negative input); O(n² · k) or worse presented as the best possible; "proven" from random tests.

## P2. `QuoteBook.quote_all` (performance engineer)

- **What is slow:** `_quote_one` holds the lock across `carrier.quote`, a 40 ms network request, so the 8 workers run one at a time: about N × 40 ms instead of N × 40 ms / 8 (measured: 40 shipments take 1.62 s with the lock, about 0.2 s without). The lane deduplication loop is O(k²) for k ≤ 6 stops: not worth changing.
- **Expected:** profile (wall time against CPU time, or timing with a fake carrier), classify the bottleneck as waiting on a lock around I/O (rule 10, the USE method in Phase 2), and recommend shrinking the critical section: compute lanes and call the carrier outside the lock; hold it only to store the price and increment `requests_made`.
- **Behavior:** this lets up to 8 requests reach the carrier at once where the code sends one at a time today. The client is documented as thread-safe, but load on the carrier and its rate limits change (`BEHAVIOR-TRAPS.md`, "Changed concurrency"). It belongs under "Behavior changes for review" (or unverified equivalence for the threading, unless a stress test or concurrency checker covers it) and must not be applied on "apply all."
- **Pass:** bottleneck named as the lock held across I/O, with evidence; the fix proposed and listed for review; `requests_made` and the price stay under the lock in the proposal; the deduplication loop reported as not worth changing.
- **Fail:** optimizing the deduplication loop as the main item; "add more workers"; applying the lock change without item-by-item approval; moving `requests_made += 1` outside the lock (a data race).

## P3. `business_days_between` (formal-methods engineer)

- **What is slow:** one loop step per day, and two holiday sets built per day: 115 µs for a 30-day range, about 4 minutes a night at 2 million calls.
- **Good answers:** a prefix table over the supported range (36,525 dates: business days before each date), so a call is two lookups, O(1), with bounded memory; or week arithmetic plus a holiday count.
- **Verification is the point of this case.** The domain is finite: every date from 2000-01-01 to 2099-12-31.
  - **Level 4 is cheap:** with a prefix table, `f(start, end) = P(end) − P(start)` for `end > start`. Checking P against the original's day-by-day definition on every date in the domain, plus the additivity of the original, covers every pair. Stating that argument and running it is a proof over the whole domain.
  - **Level 3 at least:** all start dates in the domain with every range length up to a stated bound (for example 0 to 60 days), against the original.
- **Contract traps:**
  - Out-of-range dates must still raise `ValueError` (with the date in the message). A table lookup without the check returns wrong answers silently for dates before 2000 (Python's negative indexes) and raises `IndexError` after 2099.
  - `end <= start` returns 0.
  - `LAST_SUPPORTED` itself is a valid `end`: the table needs an entry for it.
  - A Saturday holiday on January 1 is observed on December 31 of the previous year (2021-12-31, 2010-12-31): the table must include it.
- **Pass:** contract written before the change; verification level 3 or 4 reported with the exact domain (and the argument, for level 4); the error contract kept; the probe finds no mismatch.
- **Fail:** random tests only, reported as "verified" without a level, or "proven"; any mismatch in the probe; `IndexError` or a silent wrong answer outside the supported range.

## P4. `nearest_depot` (experimental scientist)

- **Facts:** 12 depots (a fixed list), called once per order: 9.4 µs per call, about 19 s for 2 million orders a night (measured).
- **Expected:** rule 8. The scan is over a fixed list of 12, so no asymptotic improvement exists at this size. Constant-factor options (precomputing each depot's radians and cosine, comparing the haversine term `a` instead of the full distance) may give a measurable gain; a spatial index (k-d tree, ball tree) will be slower at n = 12, and a k-d tree on raw latitude and longitude uses the wrong metric for great-circle distance (wrong answers near the poles and the antimeridian).
- **Pass:** a written prediction before measuring; a benchmark with repeated, alternating runs; any change kept only if the gain exceeds the noise, with exact results (same depot, including ties, where the first listed wins); rejected attempts listed under "Tried and rejected"; "not worth changing" is also a pass when backed by the 19-seconds-a-night figure.
- **Fail:** a spatial index recommended as a win; a change reported as faster without a measurement, or with a gain inside the noise; comparing squared planar distances (changes results).

## P5. `repeated_ids` (hostile input)

- **What is slow:** `list.count` for every element: O(n²). At 100,000 IDs a request (the API's maximum), minutes per request.
- **The trap:** the obvious fix, a `dict` or `Counter`, is O(n) expected, but the IDs come from the client and CPython hashes integers to themselves modulo 2⁶¹ − 1. A client that sends multiples of that number makes every ID collide: measured 2.1 s at 20,000 IDs, quadratic again. String hashing in CPython is randomized; integer hashing is not.
- **Expected:** the exposure check marks the input untrusted (`WORKFLOW.md`, Phase 2, step 7), and the agent judges by the worst case: sort, then scan for runs (O(n log n) worst case, 0.3 ms on the same colliding input), which also produces the ascending order directly. A keyed transformation of the IDs before hashing is acceptable if it is explained.
- **Pass:** exposure stated; worst-case bound reported; sort-based (or keyed) solution; adversarial benchmark with colliding IDs, or the collision risk stated with its cause.
- **Fail:** a plain `dict`, `set`, or `Counter` applied or recommended without addressing integer hash collisions.

## P6. `unmatched_parcels` (control)

- **Expected:** build a set from the manifest once; keep scan order and repeats. O(s · m) → O(s + m) expected. Straightforward. Parcel codes are strings from the company's own scanners, and string hashing is randomized anyway.
- **Pass:** applied with order and repeats kept; reported in the compact format (`REPORTING.md`).
- **Fail:** order changed, repeats dropped, or a full-format item with three padded candidates.

## PW1. `sla.py` (write mode)

Run in its own fresh run directory. Prompt:

```
Add a function longest_on_time_streak(deliveries, budget_minutes) in a new file logistics/sla.py. deliveries is one driver's deliveries in order, each a (promised, delivered) pair of datetimes. Return the length of the longest run of consecutive deliveries whose total late minutes is at most budget_minutes. A delivery's late minutes are the whole minutes after its promised time; early or on-time deliveries count as 0. Add tests.
```

- **Expected mode:** write mode, stated at the start.
- **Size:** 4,000 deliveries per driver per quarter (`volumes.py`).
- **Expected:** a sliding window over late minutes: O(n). Valid only because late minutes are never negative (early deliveries count as 0); using raw `delivered − promised` would make the window invalid.
- **Pass:** O(n) sliding window with the non-negativity stated as its assumption; tests compare it with a brute-force reference version in the test file on generated inputs (the reference-version rule in `WRITING-NEW-CODE.md`), plus edge cases (empty list, budget 0, all late, all early); the verification level in the summary; "Performance decisions" list; no existing file changed.
- **Fail:** the brute-force version shipped; no reference version in the tests; negative late minutes allowed into the window.
