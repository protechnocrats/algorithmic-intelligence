# Optimization report: clinic (Java)

Mode: report. No source file was changed. Bug log: `BUGS-FOUND.md`.

## Test suite baseline

`bash test.sh`: **12 passed, 0 failed**, before analysis. No failing tests.

## Scope

- **Inspected:** all 30 files in `src/main/java/com/example/clinic/`. `ClinicTest.java` was searched for which functions it covers; it was not reviewed line by line.
- **Not inspected:** the test harness in `src/test/java/com/example/clinic/testing/` (Runner, Assert, Test).
- **Sizes:** the only sizes are the stated workloads in `Volumes.java` comments. None were measured in production.
- **Measurements:** run in scratch programs under `/tmp/cxo` (outside the project). Project files were not modified.
- **Project shape:** no build descriptor, no DI configuration, no `META-INF`. Most public functions have no caller in this repository.

## Reachability

No in-repo production caller exists for `RoomPlanner`, `Ledger`, `Supplies`, `PartnerImport`, `SessionCalendar`, `CodeFormatter.label`, `ReminderSender`, `RosterService`, `Availability`, or `ChartViewer`. Their only callers are tests. Each is a public API whose caller is outside the repository. Call frequencies below come from the `Volumes.java` comments, which name the jobs and endpoints.

**Question for the developer:** which jobs or endpoints call each of these, and how often? The answers decide the ranking of items with unknown frequency.

## Ranked items

Labels: **measured** (a benchmark was run) or **estimated** (complexity analysis or workload arithmetic).

### OPT-1. Repeated-visit check is quadratic on untrusted uploads

- **Where:** `PartnerImport.java:14`, `repeatedVisits`, loops at `:16` and `:19`. Reached from the partner import endpoint, once per upload. Caller is outside the repo. Upload size up to 200,000 rows (`Volumes.PARTNER_UPLOAD_ROWS_MAX`).
- **Contract:** Requires a non-null list. Returns each `VisitKey` that occurs at least twice, once each, in order of first appearance. No side effects. Equality is the record's `equals`.
- **Cost now:** Time O(n²) worst case (all rows distinct: n(n−1)/2 `equals` calls). The `repeated.contains` check adds O(n·r), r = number of repeated visits. Space O(r). Bottleneck: CPU. Exposure: **untrusted input** (the Javadoc says the upload "comes straight from the partner's request body").
  - Measured: n = 16,000 distinct keys takes 438 ms (single run, includes JIT warm-up).
  - Estimated: n = 200,000 takes about (200/16)² × 438 ms ≈ 68 s per upload, single-threaded.
- **Lower bound:** Ω(n log n) worst case. Basis: proven in the comparison (algebraic decision tree) model. The output is empty exactly when all keys are distinct, so the problem reduces to element distinctness, which has this bound (Ben-Or 1983; reduction checked by hand, not machine-checked). Expected-case hashing reaches Ω(n) on average, but it is unsafe here (see below).
- **Candidates:**
  1. Sort row indices stably by (`patientId`, `clinicId`). Scan equal runs of length ≥ 2 and record each run's first index. Sort those first indices ascending and emit the keys in that order. Time O(n log n) worst case; space O(n). Standard library only. **Chosen.**
  2. `HashMap` counts plus ordered output: O(n) expected. **Rejected by exposure.** `VisitKey` is a record of two `long`s, so its hash is predictable and an uploader can craft collisions. `VisitKey` is not `Comparable`, so `HashMap` tree bins do not help, and the worst case becomes O(n²).
  3. `TreeMap` with a comparator on the two fields: O(n log n) worst case, deterministic. Same bound as 1 with more allocation. Second choice.
  4. Keep the current code. Baseline.
- **Recommended:** Candidate 1. Time O(n log n) worst case, space O(n). Kind of win: **asymptotic**. Why not better: this is at the comparison lower bound. Hashing would be O(n) expected, but worst-case behavior under hostile keys is quadratic, so it is not acceptable.
- **Assumptions and risks:**
  - Comparator consistent with `equals`: true for two `long` fields.
  - Output order and uniqueness must match the original.
  - **Null elements change behavior** (reproduced, see `BUGS-FOUND.md` BUG-1). The original throws NPE depending on the position of nulls, and some lists with nulls return normally. The rewrite cannot reproduce that exactly without copying its quirks. Listed under **BC-4**.
- **Exposure, memory, dependency:** Exposure: untrusted input, so the worst case counts. Memory: O(n) per request, an index array of 200,000 ints (about 0.8 MB) plus references. Total = per-request memory × concurrent requests, and concurrency is not bounded by the code. None: standard library.
- **Prediction and verification plan:**
  - Predicted at n = 200,000 all distinct: about 0.1–0.3 s versus the estimated 68 s. Speedup 200–700×. Growth exponent 2 → about 1.1.
  - Verification planned: differential tests against the original over random inputs, plus exhaustive checks over all sequences of length ≤ 7 drawn from 3 keys. Target level: exhaustively checked to a stated bound.
- **Status:** Proposed. Item BC-4 needs a decision on null elements before applying.

### OPT-2. `minutesUntilOpen` scans minute by minute on a 40M-call nightly job

- **Where:** `SessionCalendar.java:46`, `minutesUntilOpen`, loop at `:50`, helper `isOpen` at `:56`. Reached from the referral routing job: `Volumes.ROUTING_LOOKUPS_PER_NIGHT = 40,000,000` calls per night. Caller outside the repo. Public API.
- **Contract:** Requires `0 ≤ minuteOfWeek < 10080`, else `IllegalArgumentException`. Returns the minutes until the clinic is open: 0 if open now, −1 if there are no sessions, and wraps from Sunday to Monday. Pure. Sessions are immutable (`List.copyOf`).
- **Cost now:** Time O(W·S) per call worst case, W = 10,080 minutes, S = number of sessions. Space O(1). Bottleneck: CPU. Hot: yes, 40M calls per night.
  - Measured: 0.0029 ms per call averaged over all 10,080 minutes for `outpatients()` (30,240 calls, 88 ms total).
  - Estimated: 40M × 0.0029 ms ≈ 117 s single-threaded per night. The real minute distribution of the job is unknown.
- **Lower bound:** Ω(1) per query, since the answer must be produced. Basis: workload-dependent. Preprocessing amortized over 40M queries.
- **Candidates:**
  1. Table `int[10080]` of waits, built once per `SessionCalendar` instance (about 100,000 operations). Query is a range check plus one array read: O(1). Memory 40 KB per instance. **Chosen.**
  2. Per query, for each session compute `floorMod(first − m, W)` if it does not contain `m`, and 0 if it does. Take the minimum. O(S) per query, O(1) memory. Correct for wrapping sessions. Simpler, but O(S) per query. Second choice.
  3. Sorted merged intervals with binary search and wrap handling: build O(S log S), query O(log S). Not better at S = 10. Considered and dropped.
  4. Keep the current scan. Baseline.
- **Recommended:** Candidate 1. Time O(1) per query after an O(W·S) build. Kind of win: **asymptotic** (per query, O(W·S) → O(1)). Why not better: already at Ω(1).
- **Assumptions and risks:**
  - Sessions are immutable: true (`final`, `List.copyOf`).
  - Keep the range check before the table read.
  - Keep −1 when there are no sessions.
  - Keep inclusive ends and the wrap rule (`Session.contains`).
  - `outpatients()` builds a new instance on every call. If it is called per request, each call pays the build. Cache one instance (for example a lazily built static) so the table is built once.
- **Exposure, memory, dependency:** Exposure: none (input is range-checked; no secrets; no deadline stated). Memory: 40,320 bytes per live `SessionCalendar` instance. Total = 40 KB × number of live instances; the number of calendars is small and fixed. None.
- **Prediction and verification plan:**
  - Predicted per call: from about 2.9 µs to about 5–20 ns (100–500×). Night total: from about 117 s to under 1 s (estimated). Growth: from O(W·S) to O(1).
  - Verification planned: exhaustive comparison over all 10,080 minutes for `outpatients()` and for random session sets (including wrapping sessions and the empty set). Plus a planted-difference check. Target level: exhaustively checked for the given calendar; property-checked for random session sets.
- **Status:** Proposed.

### OPT-3. `CodeFormatter.label` compiles a regex per call and scans 90,000 terms

- **Where:** `CodeFormatter.java:30`, `label`. Regex compiled inside the call (`:31`). Linear scan at `:34`. Reached from lab-result ingestion: 5,000,000 results per day across 16 threads (`Volumes.LAB_RESULTS_PER_DAY`). Caller outside the repo. Shared instance; `reload` runs monthly over `TERMINOLOGY_ENTRIES = 90,000` terms.
- **Contract:** Requires non-null `rawCode` (NPE otherwise). Returns `"CODE shortName"` for the first term (in list order) whose code equals the normalized code. Otherwise returns `"UNKNOWN " + stripped raw`. `reload` swaps the whole terminology atomically (volatile field). Each call reads the field once.
- **Cost now:** Time per call: regex compile O(|raw|) plus a constant, and for a matched code a scan of T = 90,000 `equals` calls. Space O(1) per call. Bottleneck: CPU. Hot: yes.
  - Measured, free text (regex fails, no scan): 0.64 µs per call, including the compile (200,000 calls, 128 ms).
  - Measured, matched code at the end of the 90,000-term list: 0.30 ms per call (2,000 calls, 609 ms).
  - Estimated per day: 5M × f × about 0.15 ms (average scan is half the list). The matched fraction f is unknown. For f = 10%, about 75 s of CPU per day, about 5 s wall across 16 threads.
- **Lower bound:** Ω(|raw|) per call, since the code must be read. Basis: proven trivially (reads its input). A hash index reaches O(|raw|) expected, so this is at the bound.
- **Candidates:**
  1. Immutable snapshot built in the constructor and in `reload`: the term list plus a `HashMap<String, Term>` keyed by code, filled with `putIfAbsent` so the first matching term wins. Lookup is one hash probe: O(|raw|) expected. Memory O(T), about 90,000 entries, one copy per process. **Chosen.**
  2. Precompiled `static final Pattern`. Removes the per-call compile only; the scan remains. Included in candidate 1.
  3. Sorted array of codes with binary search: O(|raw| + log T) worst case, deterministic. Memory O(T). Second choice if worst-case determinism matters more.
  4. Memo of raw → label in a bounded LRU. About 400,000 distinct raw codes per day, so memory would be about 40 MB per copy, and every `reload` must invalidate it. **Rejected:** candidate 1 already removes the cost.
- **Recommended:** Candidate 1 with 2. Time O(|raw|) expected per call. Kind of win: **asymptotic** for matched codes (O(T) → O(1)), **constant-factor** for free text (the compile). Why not better: at Ω(|raw|).
- **Assumptions and risks:**
  - Terms are trusted (loaded monthly from the terminology source). Raw codes only key lookups and cannot add entries, so an attacker cannot build long collision chains among the terms. Expected O(1) holds (rule 9).
  - "First matching term wins": keep it with `putIfAbsent`.
  - **Null term codes:** the original throws NPE only when a scan reaches a null code. A hash index would not throw. Keep the linear scan whenever any code is null, so behavior is identical.
  - Snapshot consistency: publish the list and index together in one volatile write, so a label never sees new terms with an old index.
  - Regex: `^\s*([A-Za-z]+)[:\s-]*(\d{1,7})[\s-]?(\d)\s*$` has bounded backtracking (the `\d{1,7}` bound). It is not changed.
- **Exposure, memory, dependency:** Exposure: raw codes are external lab text but only key lookups; the regex has bounded backtracking. Memory: about 90,000 map entries per `CodeFormatter`. The index must be shared; one per process, not one per ingestion thread (16 copies would be 16×). None: standard library.
- **Prediction and verification plan:**
  - Predicted for matched codes: 0.15–0.30 ms → about 0.1–0.3 µs, roughly 1000×. For free text: 0.64 µs → about 0.2–0.4 µs, 2–3×.
  - Verification planned: differential tests on random raw strings and terminology sets, including null codes, duplicate codes (first match), and reload visibility. Exhaustive over all raw strings of length ≤ 6 from a 9-character alphabet of the regex's relevant classes. Target level: exhaustively checked to a stated bound.
- **Status:** Proposed.

### OPT-4. `RoomPlanner.roomsNeeded`: exponential exact search for interval conflicts

- **Where:** `RoomPlanner.java:17`, `roomsNeeded`. Search in `fewestRooms` (`:60`) and `assign` (`:69`). Reached from the department's daily room plan, `Volumes.APPOINTMENTS_PER_ROOM_PLAN = 400`. Caller outside the repo.
- **Contract:** Returns the fewest rooms such that no two overlapping appointments share a room. Intervals are half-open: `a.end == b.start` is not a conflict. Throws `IllegalArgumentException` for `end ≤ start`, checked first. Empty list returns 0. Returns only the count.
- **Cost now:** Time O(n²) to build the conflict matrix, then for each k = 1..n an exact backtracking search that is exponential in the worst case. Space O(n²) booleans (160,000 bytes at n = 400). Bottleneck: CPU.
  - Measured: n = 20 takes 43 ms; n = 30 takes 9.5 s; n = 40 did not finish within 20 s (run abandoned). Random intervals, starts in [0, 600), lengths 10–70 minutes.
  - At n = 400 the code is effectively unbounded.
- **Lower bound:** Ω(n log n) in the comparison model. Basis: proven, by reduction from ε-closeness (Ben-Or 1983), using unit intervals: "one room suffices" iff no two starts are within distance < 1. Checked by hand, not machine-checked.
- **Candidates:**
  1. Sweep: sort the endpoints, with ends before starts at equal times. The running count's maximum is the answer, because interval graphs are perfect and χ equals the maximum overlap. Time O(n log n), space O(n). **Chosen.**
  2. Greedy by start time with a min-heap of end times. Same count, and it also yields a room assignment. Checked against the exact search on 3,000 random instances with n ≤ 12: all match. Second choice if an assignment is needed.
  3. Keep the backtracking, adding symmetry breaking and starting k at the maximum overlap. Still exponential worst case, and the measured n ≥ 40 cases would still time out. **Rejected.**
  4. Minute-indexed difference array: O(n + T) with T = 1440. **Rejected:** the code does not enforce `start/end ∈ [0, 1440]`. Adding that check would change behavior for out-of-range input.
- **Recommended:** Candidate 1. Time O(n log n), space O(n). Kind of win: **asymptotic**. Why not better: at the proven Ω(n log n) bound in the comparison model.
- **Assumptions and risks:**
  - The conflict relation is exactly interval overlap, as the code defines it (`i ≠ j`, `a.start < b.end`, `b.start < a.end`). Verified by reading the code.
  - Half-open ties: process ends before starts at the same minute.
  - Keep the validation loop and its message, so the same first invalid appointment throws the same exception.
  - `appointments.get(i)` on a `LinkedList` would make the current code worse; moot after the rewrite.
- **Exposure, memory, dependency:** Exposure: none (scheduling data from the internal planner). Memory: O(n) instead of O(n²). None: standard library.
- **Prediction and verification plan:**
  - Predicted: n = 30 from 9.5 s to under 10 µs (over 10⁵×). n = 400 from unbounded to under 1 ms. Growth from exponential to about n log n.
  - Verification planned: exhaustive over all interval sets with n ≤ 4 and endpoints in [0, 4], plus randomized comparison against the exact search for n ≤ 15. Target level: exhaustively checked to a stated bound.
  - Achieved so far: tested only (the 3,000-instance greedy check above, in scratch code).
- **Status:** Proposed.

### OPT-5. Nightly reminders are sent one request at a time (behavior change)

- **Where:** `ReminderSender.java:21`, `sendAll`, loop at `:24`, pause after each send. Reached from the nightly reminder job, `Volumes.REMINDERS_PER_NIGHT = 30,000`. Caller outside the repo.
- **Contract:** Sends each reminder in order, one request each. Counts successes. Collects rejected ids in send order (a `GatewayException` counts as a rejection). Other exceptions propagate. Interrupt → `IllegalStateException`. Pause `pauseMillis` (100 ms in production) after every message.
- **Cost now:** 30,000 serial requests. Each request takes about 30 ms and is followed by a 100 ms pause. Estimated total: 30,000 × 0.13 s ≈ 65 minutes per night. Bottleneck: network and rate limit, not CPU. The provider allows 10 requests per second and suspends the account for an hour if exceeded, so the rate limit is a hard constraint.
- **Lower bound:** ⌈R / 50⌉ requests if every batch succeeds (each request carries at most 50 messages). Basis: workload-dependent, since rejection is per message. No general bound.
- **Candidates:**
  1. `sendBatch` in chunks of 50. If a batch is rejected (all or nothing), send its messages one at a time, in order. With a 1% rejection rate, about 39.5% of batches are rejected. Estimated requests: 600 batch requests + 11,850 individual sends = about 12,450, roughly 27 minutes at the current pacing. **Chosen, pending approval (BC-1).**
  2. Batch with no fallback: 600 requests, but a rejected batch loses up to 49 good messages. **Rejected** (incorrect).
  3. Parallel requests. The 10 requests/second limit caps throughput, so this does not help and risks suspension. **Rejected.**
  4. Keep serial sending. Baseline.
- **Recommended:** Candidate 1, only after approval of BC-1. Kind of win: **work avoided** (fewer requests), not a complexity reduction. Estimated about 2.4× less wall time.
- **Assumptions and risks:** Provider decisions for a message are the same whether it is sent alone or in a batch. This is unknown, so the change is a known behavior change (BC-1). Pacing must stay at or below 10 requests per second. The 100 ms pause must apply per request, batch or single.
- **Exposure, memory, dependency:** Exposure: none in the code. Memory: one batch of 50 messages. None.
- **Prediction and verification plan:**
  - Predicted: 65 min → about 27 min (estimated), request count 30,000 → about 12,450.
  - Verification: tested against a fake gateway with random rejection patterns (compare `sent` and `rejectedIds`). The real provider's batch behavior cannot be tested here.
- **Status:** Awaiting developer review (BC-1).

### OPT-6. `Ledger.rangeTotals` sums each range from scratch

- **Where:** `Ledger.java:15`, `rangeTotals`, outer loop `:17`, inner sum `:23`. Reached from the statement run: `LEDGER_ENTRIES_PER_ACCOUNT = 1,000,000`, `RANGES_PER_STATEMENT_RUN = 20,000`. Caller outside the repo.
- **Contract:** Returns `totals[i]`, the sum of `amounts[from..to)` computed left to right starting from `0.0`, in range order. Throws `IllegalArgumentException` for the first invalid range in order. Empty range returns `+0.0`.
- **Cost now:** Time O(Σ(to − from)) = O(R·L) worst case: 20,000 × 1,000,000 = 2·10¹⁰ additions. Space O(R). Bottleneck: CPU. Hot: once per statement run.
  - Measured: 200 random ranges (starts among 24 boundaries) take 44 ms, about 0.44 ns per addition. 50 ranges take 19 ms (includes warm-up).
  - Estimated worst case: 2·10¹⁰ × 0.44 ns ≈ 9 s per run. Estimated for the measured mix: about 4 s.
- **Lower bound:** Ω(R + L) in the real-arithmetic model, since the inputs must be read. For bit-exact `double` results the bound is **unknown**; this report does not claim one.
- **Candidates:**
  1. Group ranges by `from`. For each group, make one left-to-right pass from `from` to the largest `to` in the group, reading the running total at each requested `to`. The partial sums from the same start are the same sequence the original computes, so results are **bit-identical**. Time O(D·L + R log R), where D = distinct starts. Space O(R). **Chosen.** D ≤ 24 is stated in `Volumes` but not enforced. If D = R, this is no better than today.
  2. Prefix sums: total = P[to] − P[from]. Time O(L + R). Results **differ in low-order bits** (different rounding and cancellation). This is a known behavior change: **BC-3**, not recommended unless approved.
  3. Segment tree or block sums: same rounding issue as 2. **Rejected.**
- **Recommended:** Candidate 1. Kind of win: **asymptotic** when D is small (R·L → D·L).
- **Assumptions and risks:**
  - Validate every range first, in order, so the same first invalid range throws. The original's earlier sums have no observable effect other than time.
  - The start value must be `+0.0`, not `-0.0`, so that empty and all-negative-zero sums match the original.
  - `amounts` must not be mutated during the call.
- **Exposure, memory, dependency:** Exposure: none (ranges come from statement configuration). Memory: O(R) for the grouping. None.
- **Prediction and verification plan:**
  - Predicted with D = 24, L = 1M: about 24M additions ≈ 10 ms, versus 4–9 s now: roughly 400–900×.
  - Verification planned: bit-exact comparison (`Double.doubleToRawLongBits`) against the original, using random data, `±0.0`, NaN, infinities, subnormals, duplicate ranges, and first-invalid-range ordering. Exhaustive over short arrays and up to 3 ranges. Target level: exhaustively checked to a stated bound.
- **Status:** Proposed.

### OPT-7. Roster fetches one patient per round trip (behavior change)

- **Where:** `RosterService.java:19`, `dailyRoster`, loop at `:21` calling `directory.fetch` once per appointment. Reached from the daily roster print: about 2,000 appointments (`Volumes.APPOINTMENTS_PER_DAILY_ROSTER`), once per morning. Caller outside the repo.
- **Contract:** One line per appointment, in order. Throws `PatientNotFoundException` for the first appointment (in order) whose patient has no record.
- **Cost now:** 2,000 serial round trips. Estimated at 2 ms p50, about 4 s; at 15 ms p99, about 30 s (latencies from the `PatientDirectory` Javadoc, not measured). Bottleneck: network. Frequency: once per day, so this is latency, not CPU. n = 2,000 is not tiny, so it is kept.
- **Lower bound:** ⌈n / 500⌉ round trips, given the `fetchAll` cap of 500 ids per call. Basis: proven under the stated API. For n = 2,000 that is 4.
- **Candidates:**
  1. Chunk the distinct ids into groups of 500, call `fetchAll` for each chunk, build lines in appointment order, and throw `PatientNotFoundException` for the first missing id in order. 4 round trips. **Chosen, pending approval (BC-2).**
  2. Parallel `fetch` calls: same number of round trips, more load on the service. **Rejected.**
  3. Cache patients across days: a staleness problem, not a complexity fix. **Rejected.**
- **Recommended:** Candidate 1 after approval. Kind of win: **asymptotic in round trips** (n → ⌈n/500⌉). Estimated 4–30 s → under 0.1 s.
- **Assumptions and risks:** `fetchAll` returns records for the requested ids and leaves out missing ones (per its Javadoc). The change alters the call pattern and failure timing (BC-2).
- **Exposure, memory, dependency:** Exposure: none. Memory: at most 2,000 records. None.
- **Prediction and verification plan:**
  - Predicted: 4 requests instead of 2,000.
  - Verification: the test suite already has a fake directory with `fetchAll`. Differential tests can compare lines and the exception. Call count and failure timing will differ, which BC-2 covers.
- **Status:** Awaiting developer review (BC-2).

### OPT-8. `weeklyRoomsNeeded`: exact coloring of circular arcs is NP-hard

- **Where:** `RoomPlanner.java:40`, `weeklyRoomsNeeded`; same search as OPT-4 (`fewestRooms` `:60`, `assign` `:69`). Reached from the weekly clinic room plan: `Volumes.WEEKLY_SLOTS_PER_CLINIC = 60`. Caller outside the repo.
- **Contract:** Returns the fewest rooms for recurring weekly slots that wrap around the week. Throws `IllegalArgumentException` for a start or length outside the week, checked first.
- **Cost now:** Time O(n²) for the matrix plus an exponential exact search worst case. Space O(n²). Bottleneck: CPU.
  - Measured (random slots): n = 10 takes 1.1 ms; n = 20 takes 2.4 s; n = 30 takes 0.85 s (instance variance); n ≥ 40 did not finish within 20 s.
  - At n = 60 the code does not finish in practice.
- **Lower bound:** No polynomial exact algorithm unless P = NP. Basis: **conditional**. Coloring circular-arc graphs is NP-complete (Garey, Johnson, Miller, Papadimitriou 1980). That reference is from memory and was **not checked** in this session.
- **Candidates:**
  1. Keep the exact search, with two result-preserving prunings:
     - Symmetry breaking: rooms are interchangeable, so only open the next unused room index.
     - Start k at a clique lower bound: the maximum number of slots covering one minute. Those slots pairwise conflict, so fewer rooms cannot work.
     Still exponential worst case. Chosen as the smallest exact change. Gain is measured after the change, not predicted here.
  2. Branch and bound with DSATUR ordering and the clique bound. Exact, usually much faster than plain backtracking at n = 60. More code. Candidate if 1 is insufficient.
  3. Exact ILP or SAT solver. **New dependency: needs developer permission** (rule 7).
  4. First-fit greedy coloring: O(n²), not exact, may report too many rooms. **Rejected:** behavior change.
- **Recommended:** Candidate 1 now, then measure at n = 30, 40, 60 with realistic schedules. Kind of win: **constant-factor / work avoided** in typical cases. It is not a complexity reduction; the worst case stays exponential.
- **Assumptions and risks:**
  - The clique bound holds: slots that share a minute pairwise conflict under the code's definition.
  - Symmetry breaking holds because room labels carry no meaning.
  - Behavior: count only, so results must match exactly.
- **Exposure, memory, dependency:** Exposure: none. Memory: n² booleans, 3,600 bytes at n = 60. None for candidate 1.
- **Prediction and verification plan:**
  - Predicted for candidate 1: 10–100× at n ≈ 30, growth still exponential. Whether n = 60 finishes is **unknown**.
  - Verification planned: differential tests against the original for n ≤ 12 with exact result equality, plus exhaustive small cases. Target level: exhaustively checked to a stated bound.
- **Status:** Proposed. Ask the developer whether 60-slot clinics occur and how often.

### OPT-9. `Supplies.notStocked` checks each item with `List.contains`

- **Where:** `Supplies.java:11`, `notStocked`, loop at `:13`. Reached from ward supply order processing: up to 20,000 items per order against up to 30,000 stocked items (`Volumes`). Caller outside the repo. Frequency per order unknown.
- **Contract:** Returns the order items not in the ward stock, in order, repeats kept. Uses `equals`. Does not change its inputs.
- **Cost now:** Time O(n·m) = 6·10⁸ string comparisons worst case (no matches). Space O(n). Bottleneck: CPU.
  - Measured: 20,000 × 30,000, no matches: 985 ms. 5,000 × 7,500: 84 ms. Ratio consistent with quadratic growth.
- **Lower bound:** Ω(n + m), since both lists must be read. Basis: proven trivially. Expected-case hashing reaches it.
- **Recommended:** `HashSet` built once from `wardStock`, then O(1) expected lookups per item. Time O(n + m) expected, space O(m). Kind of win: **asymptotic**. Why not better: at the bound. The catalog is trusted (the Javadoc says "the hospital's own catalog"), so expected-case hashing is acceptable (rule 9). Second choice: sorted copy with binary search, O(m log m + n log m) deterministic.
- **Assumptions and risks:** String `equals`/`hashCode` are consistent. `null` elements behave the same in `HashSet` and `ArrayList`. The returned list stays an `ArrayList`.
- **Exposure, memory, dependency:** Exposure: none (trusted catalog). Memory: a transient set of up to 30,000 strings per call, about 2–3 MB. None: standard library.
- **Prediction and verification plan:** 985 ms → about 2–5 ms (200–500×). Growth from quadratic to linear. Verification planned: differential tests with duplicates, nulls, and empty lists; exhaustive over all lists of length ≤ 4 from `{A, B, null, ""}`. Target level: exhaustively checked to a stated bound.
- **Status:** Proposed.

### OPT-10. `Availability.isAvailable` makes two round trips per call (caller advice)

- **Where:** `Availability.java:17`, `isAvailable`: one `rosteredDays` call and one `leaveDays` call (about 5 ms each). No in-repo caller.
- **Contract:** True iff the doctor is rostered on the day and not on leave. Unchanged.
- **Cost now:** 2 round trips per call. A caller that loops over doctors and days pays 2·N·D round trips.
- **Recommended:** no change in this repo. Callers should call `rosteredDays` and `leaveDays` once over the whole range, then check membership. That is 2 round trips per doctor regardless of days.
- **Status:** Skipped in this repo (caller not in repo). Advice only.

## Not worth changing

- **`ChartViewer.latestEntries` / `ChartRepository`** (`ChartViewer.java:11`, `ChartRepository.java`): per-request cache. At most 3 distinct charts per request (`Volumes.DISTINCT_CHARTS_PER_VIEWER_REQUEST_MAX`), so at most 3 store queries (about 9 ms). The cache already bounds the work by distinct charts, and the path is per request but small.
- **`RosterService.clock`** (`RosterService.java:28`): `String.format` per line. About 2,000 calls per daily roster, estimated 1–2 ms in total. Cold (once per day) and small.

## Behavior changes for review

Nothing here is applied. Each item needs the developer's explicit approval.

### BC-1. Batch reminder sends (OPT-5)

- **Location:** `ReminderSender.java:21`, `sendAll`.
- **Behavior before:** One `send` request per reminder, 100 ms pause after each. For 3 reminders, that is 3 requests, each message judged alone.
- **Behavior after:** Messages go in batches of 50 via `sendBatch`. If a batch is rejected, its messages are sent one at a time. For the same 3 reminders, that is 1 request if the batch succeeds. The number and timing of provider requests changes.
- **Who could notice:** The SMS provider (request count, timing, and per-message decisions), the nightly job's run time, and anyone reading send logs. The `SendReport` should match only if the provider decides per message the same way in batches.
- **Why it is needed:** About 65 minutes → about 27 minutes (estimated). No equivalent without a batch call.
- **Decision:** Awaiting developer review.

### BC-2. Batch patient lookup in the roster (OPT-7)

- **Location:** `RosterService.java:19`, `dailyRoster`.
- **Behavior before:** One `fetch` per appointment, in order. Stops at the first missing patient. Calls before the failure are made one at a time.
- **Behavior after:** Ids are fetched in chunks of 500 before any line is built. The exception for the first missing patient (in order) is the same. But all chunks are fetched first, so the number and timing of service calls differs, and if the service fails mid-way the error may be different or come after different calls.
- **Who could notice:** The hospital records service (call count and pattern), and anyone who depends on the failure timing.
- **Why it is needed:** 4 round trips instead of 2,000. No equivalent without the batch call.
- **Decision:** Awaiting developer review.

### BC-3. Prefix sums for ledger totals (OPT-6, considered)

- **Location:** `Ledger.java:15`, `rangeTotals`.
- **Behavior before:** Each total is a left-to-right sum from its own start.
- **Behavior after:** Totals are computed as prefix differences. Results differ in low-order bits, and large cancellation can make them differ more.
- **Who could notice:** Anything that compares totals exactly, such as statement reconciliation.
- **Why it is needed:** O(L + R) instead of O(D·L + R log R). The bit-identical grouping in OPT-6 already gives most of the gain, so this is **not recommended**.
- **Decision:** Awaiting developer review (not recommended).

### BC-4. Null elements in partner uploads (OPT-1)

- **Location:** `PartnerImport.java:14`, `repeatedVisits`.
- **Behavior before:** Whether a null element throws NPE depends on its position and on earlier duplicates. Reproduced: `[a, null]` throws NPE; `[null, a]` returns `[]`; `[a, null, b]` throws NPE; `[null, null]` throws NPE. (`[a, a, null]` returns `[a]` by reading the code, not run.)
- **Behavior after:** Any list with a null element and two or more elements throws NPE. A one-element list `[null]` returns normally.
- **Who could notice:** The partner import endpoint, for uploads that contain nulls.
- **Why it is needed:** Reproducing the original's position-dependent NPE exactly means copying its quirks. A parser that never produces nulls makes this moot.
- **Decision:** Awaiting developer review. Ask whether the upload parser can produce nulls.

## Tried and rejected (analysis only; nothing was built into the project)

- **Hash-based duplicate check in `repeatedVisits`:** rejected. Expected O(n), but a crafted upload can make the worst case quadratic (OPT-1).
- **Prefix sums in `rangeTotals`:** rejected unless approved, since they change low-order bits (BC-3).
- **Bounded LRU memo in `CodeFormatter.label`:** rejected. The index already removes the cost, and a memo would need invalidation on every `reload` (OPT-3).
- **First-fit greedy for `weeklyRoomsNeeded`:** rejected. Not exact (OPT-8).
- **Minute-indexed array for `roomsNeeded`:** rejected. Requires an input range the code does not enforce (OPT-4).
- **Parallel patient fetches or parallel reminder sends:** rejected. Same round trips, more load, and the 10 requests/second limit caps the send rate (OPT-5, OPT-7).

## Bugs

See `BUGS-FOUND.md`. One reproduced edge behavior (BUG-1, null elements in `repeatedVisits`), recorded as a contract question and not fixed.
