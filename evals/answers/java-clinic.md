# Answer key: java-clinic (tuning set)

Do not copy this file into a run directory. The agent must not see it.

**Tuning fixture.** Use it to find where the skill's wording fails and to improve it. Its held-out twin is `rb-clinic`: every category here has a case there with a different surface. When a change to the skill is made because of a result here, check it on `rb-clinic` before calling it an improvement.

Java 17 or newer, standard library only, no build tool: `./test.sh` compiles with `javac` and runs a minimal runner (`src/test/java/com/example/clinic/testing`). Needs a full JDK (`javac` on `PATH`, or `JAVA_HOME`). Sizes come from `Volumes.java`. Grading probe: `JAVA_HOME=<jdk> python3 -I evals/probes/java-clinic.py <run-directory>`. All measurements below: OpenJDK 25.0.4 (JetBrains Runtime), Linux x86-64, 2026-11-01.

**Citations** in this key were written from memory on 2026-11-01 and have not been rechecked against the sources. Check them before quoting them in results.

No case here has a textbook name that gives the answer away. Every case states why an agent without the skill is likely to fail it; that is the case's reason to exist.

| ID | Location | Category | Rules and files tested | Why a baseline is likely to fail |
|---|---|---|---|---|
| J1 | `RosterService.dailyRoster` | Beyond Big-O: N+1 | Rule 10, contract (errors), batch limit | Switches to `fetchAll` and drops the missing-patient contract or the 500-id limit |
| J2 | `CodeFormatter.label` | Beyond Big-O: memory | Rule 1 (bounded memory), reload contract, threads | Memoizes by raw code: unbounded, and stale after `reload` |
| J3 | `ReminderSender.sendAll` | Beyond Big-O: external limit | Bottleneck classification, rule 5 | Removes the pause or parallelizes, exceeding the provider's rate limit |
| J4 | `ChartViewer.latestEntries` | Control (looks like N+1) | Rule 8 (measure before changing) | "Fixes" an N+1 that the per-request identity map already removes |
| J5 | `RoomPlanner.roomsNeeded` | Discovery: special case | `DISCOVERY.md` (special cases, reductions), lower bound | Keeps searching a general coloring, or uses a sweep that counts back-to-back appointments as overlapping |
| J6 | `RoomPlanner.weeklyRoomsNeeded` | Discovery: honest hardness | Rule 6 (no invented bound), provenance label, verification level | Reuses the J5 sweep or greedy, which is wrong for slots that wrap around the week |
| J7 | `SessionCalendar.minutesUntilOpen` | Verification | `DIFFERENTIAL-TESTING.md` levels 3 and 4 | A precomputed table that misses the wrap from Sunday to Monday: wrong on 9 of 10,080 minutes, which random tests usually miss |
| J8 | `Ledger.rangeTotals` | Behavior trap: floating point | `BEHAVIOR-TRAPS.md` (numerical), rule 5 | Prefix sums, which change 97% of totals in the last bits |
| J9 | `PartnerImport.repeatedVisits` | Hostile input | Exposure check, `techniques/hostile-inputs.md` | A `HashMap` keyed by a record: quadratic on colliding keys, slower than the original |
| J10 | `Supplies.notStocked` | Control (straightforward) | Compact format, order and repeats | (Expected to pass either way) |
| JW1 | New `CoverageReport` (write mode, separate run) | Write mode | Calls into slow existing code, "existing code is the bottleneck: tell and ask" | Uses `rosteredDays`, which ignores leave, or changes `Availability` without asking |

## J1. `RosterService.dailyRoster` (N+1)

- **What is slow:** one `PatientDirectory.fetch` round trip per appointment: 2,000 round trips at about 2 ms each per daily roster, 4 s at p50 and up to 30 s at p99.
- **Expected:** classify it as a network round trip in a loop (rule 10). Fetch each distinct patient once with `fetchAll`, in chunks of at most 500 ids, then build lines in appointment order. 2,000 round trips become 2 for 900 distinct patients (measured by the probe's `J1-trips`).
- **Contract traps** (each checked by the probe):
  - `fetch` throws `PatientNotFoundException` for the first appointment, in order, whose patient has no record. `fetchAll` silently leaves missing ids out. A rewrite that does `map.get(id)` throws `NullPointerException` or builds a line with a null patient.
  - `fetchAll` throws `IllegalArgumentException` above 500 ids. A daily roster has up to 2,000 appointments and about 900 distinct patients, so one unchunked call fails in production but passes the fixture's three-appointment test.
  - The exception must name the first missing patient in appointment order, not in the order of a `HashSet` of ids.
- **Pass:** batching with chunks of 500, the missing-patient contract kept (checked in appointment order), probe `J1` same; the change classified as work avoided along the call chain (round trips), not as an asymptotic win.
- **Fail:** any probe difference; one `fetchAll` call with every id; a `NullPointerException` path; parallel `fetch` calls (concurrency added without approval).

## J2. `CodeFormatter.label` (bounded memory, reload contract)

- **What is slow:** every call scans the 90,000-entry terminology and compiles the regular expression: about 260 to 310 µs per label (measured), about 1,300 s of CPU per day at 5 million results.
- **Expected:** an index from code to term, built once per terminology in the constructor and in `reload`, published through the `volatile` field so that every thread sees either the old index or the new one, never a half-built map; the `Pattern` hoisted to a `static final` field. About 5 µs per label (measured with the probe's reference rewrite), memory bounded by the terminology size.
- **Traps:**
  - **Unbounded memoization.** Caching results by raw code (`ConcurrentHashMap.computeIfAbsent(raw, ...)`) is the tempting fix. Raw codes are free text: 400,000 distinct per day, few repeating (`Volumes.java`). Measured: 74 to 76 MB retained per day of distinct codes, about 1.6 GB over a typical 21-day uptime (rule 1: memory must stay bounded).
  - **Stale after reload.** A memo of labels keeps serving the old short names after `reload`; the class comment says labels must use the new terminology from the moment `reload` returns.
  - **Unsafe publication.** An index built lazily on first use from several ingestion threads, without synchronization, races.
  - **Duplicate codes.** The terminology does not promise unique codes; the original returns the first matching term. An index built with `put` returns the last (the probe checks this; `putIfAbsent` keeps the original behavior).
- **Pass:** a bounded index rebuilt on reload, safely published; first-match-wins kept; probe `J2` same and `J2-memory` near 0 MB.
- **Fail:** any probe difference (stale labels, last-wins duplicates); an unbounded cache; a cache bounded only by an arbitrary size with no hit-rate measurement presented as the main fix.

## J3. `ReminderSender.sendAll` (external rate limit)

- **What is slow:** 30,000 reminders a night at one request plus a 100 ms pause each: about 65 minutes.
- **The trap:** the pause is how the code stays under the provider's limit of 10 requests per second (`SmsGateway`'s comment: exceeding it suspends the account for an hour). Removing the pause, or sending from several threads, breaks a contract with an external system. The bottleneck is the rate limit, not the CPU or the loop.
- **Expected:** classify the bottleneck as an external limit (`techniques/queues-and-latency.md`, rule 10) and keep the request rate. The real win is fewer requests: `sendBatch` sends up to 50 messages per request, so 30,000 reminders need 600 requests (about 1 minute) instead of 30,000. `sendBatch` is all or nothing: one rejected number fails the whole batch. So either
  - present batching as a behavior change for review (failure handling and timing change), or
  - batch with a fallback that resends a failed batch one message at a time, which keeps the result (sent count, rejected ids in send order) identical; with 1% rejections about 40% of batches fail, which costs about 12,000 extra requests. **Best known:** split a failed batch in halves recursively (adaptive group testing), about 600 + 2 · log₂(50) · (rejections) ≈ 4,000 requests at 1% rejections; reporting this as a candidate is a bonus.
- **Pass:** the rate limit treated as a contract; probe `J3` same and `J3-rate` ok (the probe scales the pause down to 10 ms and checks at most 10 requests in any window of 10 pauses).
- **Fail:** `J3-rate` exceeded (pause removed, threads, a per-thread pause); batching without a fallback applied silently (rejections reported differently); the case reported as CPU-bound.

## J4. `ChartViewer.latestEntries` (control)

- **Looks like:** an N+1 (one `repository.chart` call per panel).
- **Actually:** `ChartRepository` is created per request and caches loaded charts, and a request opens at most 3 distinct charts (`Volumes.DISTINCT_CHARTS_PER_VIEWER_REQUEST_MAX`): at most 3 queries, which is already the minimum for 3 charts with a single-chart store.
- **Pass:** not worth changing, with the identity map and the per-request bound named (and, ideally, the query count measured).
- **Fail:** a batch-loading API added to `ChartStore` or the repository; the item ranked as a top finding.

## J5. `RoomPlanner.roomsNeeded` (discovery: a special case makes it easy)

- **Problem as written:** build the conflict graph and find its chromatic number by backtracking (try 1, 2, 3, ... rooms). Graph coloring is NP-hard in general, so an agent that recognizes "coloring" may stop there.
- **What makes it easy:** the conflict graph is an interval graph (appointments are intervals of one day). Interval graphs are perfect: the fewest rooms equals the largest number of appointments in progress at one moment, found by a sweep over sorted start and end times in O(n log n). Times are integer minutes, so a difference array over the day's span (1,440 minutes when every appointment lies within the day; the record does not enforce that, so fall back to sorting or offset by the minimum) gives O(n + span). Lower bound: Ω(n), to read every appointment; the difference array reaches it.
- **Measured:** the original takes 0.3 ms at 14 appointments, 85 ms at 18, 22 s at 22 (mean of five random days); at 400 appointments (`Volumes`) it never finishes. The sweep: 15 ms at 400.
- **Traps:**
  - Back-to-back appointments (one ends at 10:00, the next starts at 10:00) do not overlap: at equal times the sweep must process ends before starts. Processing starts first was wrong on 47% of 3,000 random small days.
  - A generic greedy coloring in input order is not optimal: wrong on 2.5% of the same days.
  - The `IllegalArgumentException` for an appointment that does not end after it starts must stay (the probe checks it).
- **Pass:** O(n log n) sweep, O(n + span) difference array, or greedy assignment in start order with a heap of room end times, matching outputs (probe `J5` same, including the back-to-back cases); the reduction named (interval graph, maximum overlap equals the minimum number of rooms); provenance *established* (with a source, for example interval partitioning in Kleinberg and Tardos, *Algorithm Design*, section 4.1); verification level 2 or higher.
- **Fail:** any probe difference; "NP-hard, cannot be improved" for this method; an O(n²) pairwise overlap count presented as the best possible.

## J6. `RoomPlanner.weeklyRoomsNeeded` (discovery: honesty about hardness)

- **The twin of J5:** the same backtracking, but slots recur weekly and may run past Sunday midnight into Monday. The conflict graph is a circular-arc graph. Coloring circular-arc graphs is NP-complete (Garey, Johnson, Miller, and Papadimitriou, "The complexity of coloring circular arcs and chords," *SIAM Journal on Algebraic and Discrete Methods* 1(2), 1980). The maximum overlap is only a lower bound: five slots in an odd cycle never overlap more than two at a time, but need three rooms.
- **Expected:**
  - Say that the J5 sweep does not carry over and why; report the lower bound honestly: no polynomial algorithm is known (NP-complete), so the bound is unknown beyond Ω(n).
  - Keep an exact algorithm and improve it: start the search at the maximum overlap instead of 1 (every smaller count is infeasible), order slots by start or by degree, and prune with the current best (branch and bound, DSatur-style). Or an exact exponential method (Lawler's dynamic program over subsets, O(3ⁿ), or inclusion-exclusion in O*(2ⁿ), Björklund, Husfeldt, and Koivisto, 2009), stated with its limit: 60 slots per clinic (`Volumes`) is far too many for either.
  - If a heuristic is proposed, it changes results and goes under "Behavior changes for review." A simple one with a guarantee: cut the week at one minute, give each slot that crosses it its own room (at most the maximum overlap), and solve the rest as intervals with the J5 sweep: at most 2 × the optimum.
- **Measured:** the interval greedy applied to arcs was wrong on 47 of 3,000 random small weeks (1.6%), and "maximum overlap" was wrong on 2 of 3,000 random weeks, so random testing alone may miss the hardness; the probe adds two odd cycles (5 and 7 slots) where it is always wrong.
- **Pass:** probe `J6` same; the hardness stated with its basis (or "no polynomial algorithm known," with the reason); any applied improvement labeled *derived* or *established* with a source and verified at level 2 or higher (exhaustive over small inputs is cheap here).
- **Fail:** any probe difference (a sweep, the J5 greedy, or "maximum overlap" applied); a polynomial exact algorithm claimed; "proven" from random tests.

## J7. `SessionCalendar.minutesUntilOpen` (verification over a finite domain)

- **What is slow:** each call walks forward minute by minute and checks every session at each minute: about 2.6 µs per call (measured), about 105 s per night at 40 million calls (`Volumes`).
- **Expected:** precompute, per calendar, a table of 10,080 answers (two backward passes around the week, or one pass that starts from the first open minute), then answer in O(1). Compute it once per calendar (the class is immutable).
- **The trap:** a one-pass table built backward from Sunday 23:59 without wrapping around gets the minutes after the last open minute of the week wrong. In the outpatient calendar that is Sunday 23:51 to 23:59: 9 of 10,080 minutes. Random tests miss them often: 200 random minutes miss with probability 0.84, 1,000 with probability 0.41 (computed from the measured 9 minutes).
- **Verification expected:** the domain is small, so check every minute (level 4 for a given calendar: "Proven: equal on all 10,080 minutes of the outpatient calendar"), plus the out-of-range errors. For arbitrary calendars, an exhaustive check over many generated calendars (including wrapping sessions, a one-minute session, the last minute of the week, an empty calendar, and a full week) is level 3, not 4; the report should say which claim covers what.
- **Pass:** probe `J7` same (it checks every minute of 12 calendars and the errors); the verification level named with its domain.
- **Fail:** any probe difference; "proven" or "verified" from random minutes; the error contract changed (`ArrayIndexOutOfBoundsException` instead of `IllegalArgumentException`).

## J8. `Ledger.rangeTotals` (floating point)

- **What is slow:** each range is summed from scratch: O(q · n) for q ranges over n entries. Measured: 407 ms for 2,000 ranges over 1,000,000 entries, so about 4 s for the 20,000 ranges of a statement run, per account.
- **The trap:** prefix sums (`prefix[to] − prefix[from]`) reassociate the additions. Measured: 1,931 of 2,000 totals differ from the original, by up to 2.1 · 10⁻⁶. The amounts are doubles in posting order and the totals are printed on statements, so this is a behavior change (`BEHAVIOR-TRAPS.md`, numerical).
- **Expected, either of:**
  - **Bit-for-bit:** statement ranges start on at most 24 period boundaries (`Volumes.STATEMENT_PERIODS_PER_RUN`). Group ranges by `from`, sort each group by `to`, and extend one running sum per group from left to right: every total is the same sequence of additions as before, so the result is identical. O(p · n + q log q) for p distinct starts. This is the best answer: work reused without changing a bit.
  - **Prefix sums as a behavior change for review,** with the measured size of the difference, and not applied when approval is declined. Exact alternatives (compensated or exact summation) change results too and also go to review.
- **Pass:** probe `J8` same (it includes `NaN`, infinities, `-0.0`, and cancellation cases), or prefix sums listed for review and left unapplied.
- **Fail:** prefix sums applied without approval (probe difference); Kahan summation applied silently.

## J9. `PartnerImport.repeatedVisits` (hostile input)

- **What is slow:** O(n²) on uploads of up to 200,000 rows: the original takes 2.7 s on 60,000 rows.
- **Exposure:** uploads come from partner hospitals' request bodies through the public import endpoint (the method comment): untrusted input.
- **The trap:** `VisitKey` is a record of two `long`s, and on OpenJDK a record's `hashCode` is `31 · h(patientId) + h(clinicId)` with `h(v) = (int)(v ^ (v >>> 32))` (this formula is an implementation detail; the specification only says the hash is derived from the components). A client can send keys that all hash to the same value. Since Java 8, `HashMap` turns a crowded bucket into a tree, but that only helps keys that implement `Comparable`; record keys do not, so every lookup scans the bucket. Measured (OpenJDK 25): inserting 40,000 colliding record keys takes 4.4 s, against 5.5 ms for the same keys in a `Comparable` record. In the probe, a `LinkedHashMap` count takes 10.3 s on 60,000 colliding rows, four times slower than the quadratic original.
- **Expected:** exposure stated as untrusted; judged by the worst case (rule 9); a worst-case O(n log n) method that keeps first-appearance order, for example a `TreeMap` with a comparator over both fields recording each key's first index and count, then sorting the repeated keys by first index (60 ms on the same input, measured). Making `VisitKey` implement `Comparable` restores the tree buckets' O(log n) and also works, but it changes a public type: say so.
- **Pass:** exposure and worst case stated; worst-case-safe structure applied (or the collision risk stated with its cause and measured); probe `J9` same and `J9-time` well under the original.
- **Fail:** `HashMap`, `HashSet`, or `LinkedHashMap` keyed by `VisitKey` applied without addressing collisions; "O(n) expected" reported as the worst case.

## J10. `Supplies.notStocked` (control)

- **Expected:** a `HashSet` of the ward stock, built once; order and repeats kept. O(n · m) → O(n + m) expected. Item codes come from the hospital's own catalog, so the exposure is none.
- **Pass:** applied in the compact format (`REPORTING.md`); probe `J10` same.
- **Fail:** repeats dropped or order changed; a full-format item with padded candidates.

## JW1. `CoverageReport` (write mode)

Run in its own fresh run directory. Prompt:

```
Add a class CoverageReport in src/main/java/com/example/clinic/CoverageReport.java. Its constructor takes an Availability. Its method List<LocalDate> uncoveredDays(List<Long> doctorIds, LocalDate from, LocalDate to, int minDoctors) returns, in date order, each day from `from` to `to` inclusive on which fewer than minDoctors of the given doctors are available. Add tests.
```

- **Expected mode:** write mode, stated at the start.
- **Sizes** (`Volumes`): 50 doctors per report, up to 366 days.
- **What the agent finds in existing code:** `Availability.isAvailable` costs two round trips (about 10 ms) per doctor and day: 50 · 366 · 2 = 36,600 round trips, about 3 minutes per report. `Availability.rosteredDays` covers a whole range in one round trip but ignores leave (its comment says so: payroll counts leave separately). `Availability` has no method that returns available days for a range, and its clients are private.
- **Expected:**
  - Correct results first: availability means rostered and not on leave, so `rosteredDays` alone is wrong.
  - The new code calls the slow existing code as little as it can while staying correct, which with today's `Availability` means `isAvailable` per doctor and day (it cannot be avoided without changing `Availability`).
  - The summary reports `Availability` as the bottleneck, cost along the call chain included, recommends adding a range method that combines one `rosteredDays` call and one `leaveDays` call per doctor (36,600 round trips → 100), and asks before changing `Availability` (write mode: existing code is not changed for speed without asking).
- **Probe:** `JW1` compares the result with an independent reference on 40 random cases and counts round trips.
- **Pass:** 0 mismatches; `Availability` unchanged or changed only after asking; the bottleneck and the recommended range method reported; tests compare against a simple reference.
- **Fail:** mismatches (for example `rosteredDays` used, so doctors on leave are counted as available); `Availability` or its clients changed without asking; parallel calls added.
