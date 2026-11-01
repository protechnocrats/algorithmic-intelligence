# Answer key: rb-clinic (held out)

Do not copy this file into a run directory. The agent must not see it.

**Held-out fixture.** Use it only to measure the skill, never to tune its wording. Its tuning twin is `java-clinic`: every category here has a case there with a different surface. If a result here leads to a change in the skill, check the change on the tuning fixtures, and treat this fixture as no longer held out for the next round: build a new one.

**Tests `languages/GENERIC.md`.** There is no Ruby companion file, so the agent must build the language profile itself (sort stability, hash ordering, string mutability, which sorted structures the standard library lacks). RB2's aliasing and RB8's stability are where that profile matters. Since 2026-11-01 the skill also asks, in setup, whether to save the profile to `.algorithmic-intelligence/languages/RUBY.md`. The harness declines every approval, so in a pilot run the expected behavior is: the question asked once, with the file's purpose; no file written; the profile included in the report header. A run that writes the file without asking fails the "Report mode changed no files" check.

Ruby 3.2 or newer, standard library only; tests use minitest, which ships with Ruby. `./test.sh` runs them. Sizes come from `lib/clinic/volumes.rb`. Grading probe: `python3 -I evals/probes/rb-clinic.py <run-directory>`. All measurements below: Ruby 4.0.9 (Prism), Linux x86-64, 2026-11-01.

**Citations** in this key were checked on 2026-11-01 against publisher, library, and author records (titles, venues, volumes, and the results cited). Where only secondary sources state a result, the key says so.

**Contamination note (2026-11-01).** `DISCOVERY.md` moves 13 to 17 were written after this fixture, by the same author who designed RB5 and RB6. Their examples avoid these cases' domains (coins, job ordering, vertex cover, knapsack, matching), but move 15 (find the small parameter) describes RB6's intended method in general form. Count an RB6 pass as weaker evidence than an RB5 pass, and build RB6's replacement before tuning on it.

| ID | Location | Category | Rules and files tested | Why a baseline is likely to fail |
|---|---|---|---|---|
| RB1 | `Billing#statement_lines` | Beyond Big-O: N+1 | Rule 10, contract (prices on dates, error order) | Uses `current_prices`, which ignores the service date, or fetches every history up front and raises the wrong error first |
| RB2 | `Labels#display_name` | Beyond Big-O: repeated parsing | Live-reload contract, aliasing (`BEHAVIOR-TRAPS.md`) | Memoizes the parsed file forever, or returns the cached string that a caller then mutates |
| RB3 | `Exports.append_by_clinic` | Beyond Big-O: external resource | Bounded resources (open files), append contract | Keeps one open file per clinic: 5,000 files against a 1,024 limit |
| RB4 | `TimeZones.duplicate_offsets` | Control (cold, tiny n) | Rule 8 | Rewrites an O(z²) loop over at most 5 zones |
| RB5 | `Dosing.count_windows` | Discovery: combination and assumptions | `DISCOVERY.md`, assumption checks, prediction vs measurement | Two pointers, which needs non-negative entries; the pump logs negative reversals |
| RB6 | `ProcedureRoom.best_total` | Discovery: honest hardness | Rule 6, provenance, special cases | Weighted interval scheduling, which ignores the one-booking-per-patient rule |
| RB7 | `Pediatrics.band_for` | Verification | Levels 3 and 4 over a finite domain | A binary search or table that resolves the formulary's overlap the other way: wrong on 2 of 54,751 ages |
| RB8 | `Triage.queue_order` | Behavior trap: sort stability | `GENERIC.md` profile (stability), contract | `sort_by { -acuity }`, which is not stable in Ruby |
| RB9 | `Pharmacy.undispensed` | Control (straightforward) | Compact format, order and repeats | (Expected to pass either way) |
| RBW1 | New `lab_alerts.rb` (write mode, separate run) | Write mode | Sizing new code, hidden ordering assumption, `GENERIC.md` (no sorted set in the standard library) | Keeps only the last date per patient and test, which is wrong when results arrive late |

## RB1. `Billing#statement_lines` (N+1)

- **What is slow:** one `price_on` round trip (about 2 ms) per line: up to 2,000 per statement (4 s), 3,000 statements a night: over 3 hours.
- **Expected:** one `price_history` call per distinct code (about 40 per statement, `volumes.rb`), cached for the duration of the call, and each line priced locally by binary search over the change dates (the latest change on or before the service date). 2,000 round trips → 40 (probe `RB1-trips`).
- **Contract traps** (each checked by the probe):
  - `current_prices` returns today's prices, not the price on the service date. It is the obvious batch method and it is wrong for any line priced before the latest change.
  - `price_on` raises `NoPriceOnDate` for a service date before the code's first price. The local lookup must raise it too, for the same line.
  - Errors surface in line order. A rewrite that fetches every code's history before pricing any line raises `UnknownCode` for a later line before the `NoPriceOnDate` that the original raises for an earlier line. Fetching each history lazily, on the code's first line, keeps the order.
- **Pass:** probe `RB1` same; round trips reported along the call chain.
- **Fail:** `current_prices` used; any probe difference; threads added.

## RB2. `Labels#display_name` (repeated parsing, live reload, aliasing)

- **What is slow:** every call parses `config/labels.yml` (2,000 entries): 5.5 to 8.9 ms per call (measured), so about 16 s per 3,000 summary rows and about 30 to 45 minutes for the 300,000 rows of a code summary.
- **Expected:** parse once per version of the file: cache the parsed hash with the file's `File.stat` (modification time, size, inode) and re-parse when it changes. A `stat` is microseconds; measured with the probe's reference rewrite, 3,000 rows take 0.02 s.
- **Traps** (each checked by the probe):
  - **Live reload.** The class comment says an edit takes effect on the next call, without a restart. `@names ||= YAML.safe_load_file(@path)` never sees an edit.
  - **Deleted file.** The original raises `Errno::ENOENT` when the file is gone; a cache must not keep answering.
  - **Aliasing.** `CodeSummary.rows` appends `" (discontinued)"` to the returned name in place, and `code_summary.rb` has no `frozen_string_literal` comment. The original returns a fresh string per call. A cache that returns its own string lets the first discontinued row corrupt every later row for that code. Return a copy (`dup`), or freeze the cached strings and check every caller (freezing breaks `CodeSummary`, which is a behavior change).
- **Pass:** probe `RB2` same; the staleness and the aliasing named in the contract.
- **Fail:** any probe difference; reload behavior changed silently.

## RB3. `Exports.append_by_clinic` (open files)

- **What is slow:** one open and close per row, 2,000,000 rows a night. Measured on a local disk: 9.6 µs per row, about 20 s; the comment says `dir` is an NFS mount, where every open and close costs a round trip for close-to-open consistency (typically 0.5 to 2 ms), so 15 to 60 minutes.
- **Expected:** group the rows by clinic, keeping each clinic's row order, and open each clinic's file once in append mode: 5,000 opens instead of 2,000,000.
- **Traps** (each checked by the probe, which lowers the open-file limit to 256 and writes to 3,000 clinics):
  - **Open-file limit.** Keeping one open file per clinic (`Hash.new { |h, id| h[id] = File.open(...) }`) needs 5,000 open files; the export worker's limit is 1,024 (`volumes.rb`). It fails with `Errno::EMFILE`.
  - **Append, not truncate.** Files from earlier runs are kept: mode `"a"`, not `"w"`.
  - **Row order within each file** stays the input order.
- **Pass:** probe `RB3` same; the bottleneck classified as I/O (system calls, NFS round trips), not CPU.
- **Fail:** any probe difference; one handle per clinic held open at once.

## RB4. `TimeZones.duplicate_offsets` (control)

- **Expected:** not worth changing: at most 5 zones per clinic (10 pairs), run when an administrator saves a clinic's settings. Leave it.
- **Pass:** left alone, reported briefly or not at all.
- **Fail:** rewritten, or reported as a top finding.

## RB5. `Dosing.count_windows` (discovery: a combination whose obvious piece does not hold)

- **Problem:** count the windows of consecutive entries whose total is between `low` and `high` and that contain no entry above `cap`. The original is O(n³) as written (each window is sliced, summed, and its maximum taken). At 50,000 entries a month (`volumes.rb`) it does not finish in 60 s (probe `RB5-time`).
- **Measured growth:** 0.04 s at 400 entries, 0.15 s at 800, 0.61 s at 1,600: about 4 times per doubling, not 8. Slicing, `sum`, and `max` run in C, so the cubic term is still small at these sizes. An agent that predicts exponent 3 should see the miss and explain it (`BENCHMARKING.md`: a prediction that misses badly means something in the analysis is wrong).
- **Expected derivation** (`DISCOVERY.md`: change the representation, reductions):
  1. An entry above `cap` can never be in a window: split the log at those entries and solve each segment independently.
  2. Within a segment, a window's total is a difference of prefix sums, so the count is the number of pairs i < j with `low ≤ P[j] − P[i] ≤ high`.
  3. **The assumption check:** two pointers would make this O(n), but only for non-negative entries. The method comment says the pump logs negative entries for reversals, so the windows' totals are not monotone and two pointers is wrong.
  4. Count the pairs with an order-statistics structure: a Fenwick tree over the sorted distinct prefix values (or merge-sort counting). O(n log n) time, O(n) space. Ruby's standard library has no Fenwick tree or sorted multiset, so it is a short hand-written structure (`GENERIC.md`: say what the standard library lacks).
  - Lower bound: Ω(n) for reading the input; no matching lower bound is known for counting range-sum pairs, so "O(n log n), best known" is the honest claim.
  - Measured with the probe's reference rewrite: 0.06 s at 50,000 entries.
- **Pass:** O(n log n) (or a correct O(n²) with the better method named and the reason for stopping given); the non-negativity assumption checked against the code and rejected; probe `RB5` same; verification level 2 or higher (exhaustive over short lists of small values is cheap); provenance *derived* or *established* with a source (the pair-counting step is a known exercise; the combination with the cap split is not).
- **Fail:** two pointers or a sliding window applied (probe difference on negative entries); "O(n³) is required."

## RB6. `ProcedureRoom.best_total` (discovery: honest hardness)

- **Problem:** choose non-overlapping requests of maximum total value, with at most one booking per patient. The original tries every subset: 1 s at 20 requests (measured), and it never finishes at the 60 requests of a real day.
- **What looks easy:** without the patient rule this is weighted interval scheduling, O(n log n) by dynamic programming (Kleinberg and Tardos, section 6.1). That is what a model recalls. It ignores the patient rule: wrong on 324 of the probe's 500 random small days (measured with that rewrite).
- **What it is:** with several alternative intervals per patient and at most one chosen per patient, it is the job interval selection problem (JISP). Spieksma shows that, unless P = NP, it cannot be approximated arbitrarily well in polynomial time (F. Spieksma, "On the approximability of an interval scheduling problem," *Journal of Scheduling* 2(5):215–227, 1999); later papers cite it as MAX SNP-hard even with two intervals per job. In particular it is NP-hard. No polynomial exact algorithm is known.
- **Expected:**
  - Say that the textbook dynamic program does not apply and why; report the hardness with its basis.
  - Improve the exact algorithm using the workload: only patients with alternative times need to be tracked, and there are at most 12 per day (`volumes.rb`). Weighted interval scheduling with a bitmask over those patients: state (requests sorted by finish, set of tracked patients used), O(n · 2ᵏ · log n) for k tracked patients. Measured with the probe's reference rewrite: 0.02 s for 60 requests with 12 tracked patients.
  - Label it *derived* and verify it at level 2 or higher (exhaustive against the original on small days is cheap).
- **Pass:** probe `RB6` same; hardness stated (or "no polynomial algorithm known," with the reason); the 2ᵏ dependence and its limit stated.
- **Fail:** any probe difference (the plain weighted-interval program); a polynomial algorithm claimed; "proven" from random tests.

## RB7. `Pediatrics.band_for` (verification over a finite domain)

- **What is slow:** a linear scan of the 30 formulary bands: 1.2 µs per call (measured), about 50 s per night at 40 million dose checks (`volumes.rb`).
- **Expected:** a precomputed table of all 54,751 ages, or a binary search over band boundaries, built so that overlaps resolve as the original does: the first matching band in formulary order.
- **The trap:** the formulary's bands overlap: "infant, 6-12 months" runs to day 366 and "toddler, 1-2 years" starts at day 365. The original returns the infant band for days 365 and 366. A binary search for the last band starting on or before the age returns the toddler band: wrong on 2 of 54,751 ages. A random test of 1,000 ages misses both with probability 0.96 (computed from the measured 2 ages).
- **Verification expected:** check every age from 0 to 54,750 (level 4: "Proven: equal on the whole domain"), plus the errors for out-of-range and non-integer ages (the probe checks `-1`, `54,751`, `3.0`, `"5"`, `nil`, and `2**70`).
- **Bonus:** the overlap reported as a suspected formulary error in `BUGS-FOUND.md` (rule 4: documented, not fixed).
- **Pass:** probe `RB7` same; level and domain stated.
- **Fail:** any probe difference; "verified" from random ages.

## RB8. `Triage.queue_order` (sort stability)

- **What is slow:** insertion into an array: O(n²). Measured: 0.23 s for 5,000 waiting patients, recomputed 240 times a minute across the boards (`volumes.rb`): about 55 s of CPU per minute.
- **The trap:** the insertion keeps arrival order among equal acuity, and nothing but the code says so (the comment only says "highest acuity first"). Ruby's `sort_by` is not stable: measured on Ruby 4.0.9, `sort_by { -acuity }` reorders ties (the probe finds differences on 74 of 101 lists). The language profile from `GENERIC.md` (step 4: which sorts are stable) is where this should be caught.
- **Expected:** a stable sort, for example `waiting.each_with_index.sort_by { |p, i| [-p.acuity, i] }.map(&:first)`: O(n log n), 0.007 s at 5,000 (measured).
- **Pass:** probe `RB8` same; the tie order written into the contract.
- **Fail:** `sort_by` or `sort` without a tie-breaker applied (probe difference).

## RB9. `Pharmacy.undispensed` (control)

- **Expected:** a `Set` of the dispensed ids, built once; order and repeats kept. O(p · d) → O(p + d) expected. Ids come from the hospital's own system: exposure none.
- **Pass:** applied in the compact format; probe `RB9` same.
- **Fail:** repeats dropped (`uniq`), order changed, or a padded full-format item.

## RBW1. `LabAlerts.repeat_tests` (write mode)

Run in its own fresh run directory. Prompt:

```
Add a method Clinic::LabAlerts.repeat_tests(results, window_days) in a new file lib/clinic/lab_alerts.rb. results is an array of lab results in the order they arrived; each responds to patient_id, test_code and taken_on (a Date). Return, in arrival order, the results for which an earlier-arrived result has the same patient_id and test_code and a taken_on within window_days days of this one's, before or after. Add tests.
```

- **Expected mode:** write mode, stated at the start.
- **Sizes** (`volumes.rb`): 500,000 results a night, windows up to 30 days, results arriving up to 10 days late.
- **The hidden assumption:** arrival order is not `taken_on` order. Keeping only the last date per patient and test (a hash) is O(n) but wrong when a late result arrives: an earlier-arrived result may be closer in date than the last one seen. Measured with that rewrite: wrong on 177 of the probe's 300 random cases.
- **Expected:** per patient and test, keep the dates seen so far in sorted order and check the nearest earlier and later neighbors by binary search: O(n log k) for k results per key (k is small). Ruby's standard library has no sorted set (`SortedSet` left the standard library in Ruby 3.0), so a sorted array with `bsearch_index` and `insert` is the standard-library choice, O(k) per insert, which is fine for small k; a structure from a gem needs permission (rule 7). Alternatives: since windows are at most 30 days, a hash of dates per key and a check of each day in the window (O(n · w)).
- **Measured** with the probe's reference rewrite: 1.05 s for 500,000 results.
- **Pass:** 0 mismatches in probe `RBW1`; the late-arrival assumption stated; tests against a brute-force reference; sizes taken from `volumes.rb`; a "Performance decisions" list; no existing file changed.
- **Fail:** mismatches (last-date-per-key); the quadratic brute force shipped; a gem added without asking.
