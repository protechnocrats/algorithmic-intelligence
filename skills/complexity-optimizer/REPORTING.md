# Reporting

## Where reports go

For a small result (one or two items), present the report in the conversation. Otherwise ask the developer where to write it, suggesting `optimization-report/` at the project root, and ask whether it should be ignored by version control. The report has two files:

- `OPTIMIZATION-REPORT.md` — the ranked items, applied changes, benchmarks, and needs-testing list.
- `BUGS-FOUND.md` — every bug noticed. None are fixed on purpose; any removed as a side effect of an optimization are marked as such.

## Report header

Start `OPTIMIZATION-REPORT.md` (or the in-conversation report) with these sections, before any items:

- **Test suite baseline:** pass and fail counts from the run before analysis. If any tests failed, list them by name, and say which items they could affect (rule 12). In report mode the analysis continued despite them; in apply mode nothing was changed until the developer decided.
- **Scope:** what the developer asked to cover; what was inspected; and every part of that scope that was **not** inspected (modules, directories, languages, generated code), with the reason (size, time, no access, toolchain missing). Write "Everything in scope was inspected" only when that is true. Code outside the scope that was read only to trace a cost along the call chain is listed separately.
- **Language profile** (only for a language without a companion file in the skill): whether a profile saved in the project was loaded (its path and recorded version) or one was built in this session; whether it was saved or updated, at which path, and how many claims are still unverified. If the developer did not allow saving it, include the profile here in full, so the facts the analysis relied on are visible.

## Optimization item format

Rank items by expected real-world impact. Use the full format below for nontrivial items (rule 6) and for any item with behavior risks or an exposure. Straightforward items and items not worth changing use the compact format, so the report stays proportional:

```markdown
### <ID>. <Short title>

- **Location:** `path/to/File.kt:123` — `functionName`
- **Contract:** What it returns and changes, in one line.
- **Now → recommended:** O(...) → O(...) [case], at the lower bound because ...; or "not worth changing" with the size bound and why the path is cold (rule 8).
- **Evidence and verification:** Bottleneck evidence (profile, measurement, or estimate); planned or reached verification level.
- **Status:** As in the full format.
```

Full format:

```markdown
### <ID>. <Short title>

- **Location:** `path/to/File.kt:123` — `functionName`
- **Contract:** What it requires (preconditions), what it returns (including order, ties, and duplicates), and what it changes, throws, or calls (effects). State what the code and its callers show, and mark anything inferred.
- **Callers and usage:** Who calls it, how often, on which thread, typical and maximum input sizes (state the assumption and its source).
- **Reachability:** The entry point it is reached from (route, job, listener, command, UI handler, public API) and how often that runs; or "tests only"; or "unknown: no entry point found," with the places searched (dependency-injection configuration, scanning, plugin registries, routes, reflection) and the question for the developer: is this code used? Unknown reachability never means unused: the item stays, ranked below items on proven hot paths.
- **Bottleneck:** The resource that limits this code (CPU, memory, I/O, network, lock, or queue) and the evidence: profile, trace, query plan, benchmark, developer report, or static estimate only.
- **Exposure:** None, or untrusted input | secret-dependent | hard deadline, with the worst-case bound and the defense (keyed hashing, limits, constant time, preallocation) from `techniques/hostile-inputs.md`.
- **Current complexity:** Time O(...) [worst | average | amortized], space O(...), in terms of named variables. Include the cost of the functions it calls and, when callers invoke it in a loop, the total cost along the call chain.
- **Lower bound:** O(...) because ... Basis: proven (for example, must read every input) | conditional (holds only under a stated assumption, such as comparison-based sorting) | conjectured (no faster algorithm is known, such as 3SUM) | workload-dependent (follows from the measured or stated call pattern) | unknown (no bound can be established; give the reason, such as a cost dominated by a database query plan, network latency, or hardware, and the strongest bound you can support, such as "at least one pass over the input"). Never invent a bound (rule 6).
- **Difficulty:** Straightforward (strongest candidate reaches the lower bound, needs no new dependency, and has no behavior risks) | Nontrivial.
- **Candidates considered:** Straightforward: the strongest candidate and why alternatives are unnecessary. Nontrivial: at least three plausible approaches, each with how it was found (a table row, a move from `DISCOVERY.md`, or a published source) and its provenance: established (common name and a standard reference), experimental (the publication, and that it is new), or derived in this analysis (its correctness argument). Mark each citation "checked" (read in this session or listed in the skill's references) or "not checked":
  1. <Approach> — time O(...) (preprocessing and per-query separately), space O(...), notes.
  2. <Approach> — time O(...), space O(...), notes.
  3. <Approach or combination> — time O(...), space O(...), notes.
- **Recommended:** <Approach> — time O(...), space O(...). Why it wins.
- **Why not better:** At the lower bound, or what blocks the remaining gap (a dependency, a call pattern that cannot amortize preprocessing, an assumption the code does not satisfy, a measured constant factor). When no table row reached the bound, the `DISCOVERY.md` moves tried and what each gave.
- **Kind of win:** One or more of: Asymptotic (the growth rate changes, for example O(n²) → O(n log n)) | Constant-factor (same bound; fewer allocations, cache misses, branch misses, or instructions) | Work avoided (caching, batching, early exit, incremental updates). Never present a constant-factor or work-avoided win as a complexity reduction.
- **Memory bound:** What new memory is used and why it is bounded, per copy and in total: how many copies can exist at the same time (per process, worker, thread, connection, request, or tenant) and the total across all of them (rule 1).
- **Dependency needed:** None, or the library name, version, license, and why (requires developer permission).
- **Behavior risks:** Traps from BEHAVIOR-TRAPS.md that apply, and how each will be covered.
- **Assumptions:** Each assumption the technique needs and the evidence from the code that it holds.
- **Behavior changes:** None, or the exact behavior before and after (rule 5).
- **Prediction:** Written before any benchmark runs: the expected speedup at realistic n and the expected growth exponent of each version.
- **Verification:** The level reached (tested | property-checked | exhaustively checked, with the domain | proven, with the tool and what it proved; see "Verification levels" in `DIFFERENTIAL-TESTING.md`), the inputs and properties covered (edge cases, number of generated cases, seeds, sizes), tests and tools actually run with results, and behavior left unverified. "Proven" only at that level.
- **Status:** Proposed | Applied (verified: <level>) | Applied (NEEDS-TESTING, developer approved) | Applied (BEHAVIOR-CHANGE, developer approved) | Awaiting developer review | Skipped (reason) | Not worth changing (n is small and the path is cold).
- **Performance:** Measured: time and memory before and after at realistic n, larger n, and worst-case inputs where relevant, with environment, run count, median, and variance, as absolute values and percentage change, with the measured growth exponent and a comparison against the prediction. When they disagree, the explanation found. End-to-end: the share of the whole operation's time the changed code took before the change, and the resulting end-to-end saving, each labeled measured or estimated (rule 8). Estimated: the theoretical gain, labeled as estimated. If measurement could not be completed, say why; the item is not a confirmed win.
- **Reproduce:** The commands, seeds, input generators, and environment needed to rerun the tests and benchmarks.
- **Changed files:** For applied items, the exact files and functions this item changed, and the commit if commits were authorized. When commits were not authorized, this list is how the developer reviews, commits, or reverts each item on its own.
```

Also list candidates that were considered and dropped, with the reason, so the developer sees what was checked.

## Tried and rejected

Negative results are findings: they stop the next person from repeating the attempt. In `OPTIMIZATION-REPORT.md`, keep a "Tried and rejected" section for every change that was built or benchmarked and then not kept:

```markdown
- **<Short title>** (`path/to/File.kt:123`): <what was tried>. Predicted: <speedup, exponent>. Measured: <result, with environment>. Rejected because: <slower, within noise, worse memory, failed verification, behavior change declined>.
```

## Bug log format

Rule 4: document every bug and tell the developer. Never fix one on purpose. Bugs in code that is not optimized stay as they are; bugs in optimized code stay unless the optimization removes them as a side effect.

```markdown
### BUG-<N>. <Short title>

- **Location:** `path/to/File.kt:123`
- **What happens:** The incorrect behavior, with a concrete input and output, and whether it was reproduced by running the original (reproduced | suspected, not reproduced). Only a reproduced bug can be marked fixed as a side effect (rule 4).
- **Expected:** What appears to be intended, and why you think so.
- **Impact:** Who or what is affected.
- **Status:** Left as is (code not optimized: already optimal, or equivalence could not be guaranteed) | Preserved in optimized code (item <ID>) | Fixed as a side effect of item <ID> (marked `BEHAVIOR-CHANGE`; requires the failing input below, run against the original).
- **Suggested fix:** Optional, described only. Not applied (unless fixed as a side effect).
```

Tell the developer about each bug in the conversation as well as in the file.

## Behavior changes for review

Rule 5: every optimization that would change observable behavior, including changes that look like improvements, is listed at the top of `OPTIMIZATION-REPORT.md` under "Behavior changes for review" before anything is applied:

```markdown
### <ID>. <Short title>

- **Location:** `path/to/File.kt:123`
- **Behavior before:** What callers observe today, with a concrete input and output.
- **Behavior after:** What callers would observe, with the same input.
- **Who could notice:** Callers, users, stored data, or integrations affected.
- **Why it is needed:** What the optimization gains, and the best equivalent alternative if one exists.
- **Decision:** Awaiting developer review | Approved on <YYYY-MM-DD> | Declined.
```

If the developer approves, mark the code directly above the change:

```
// BEHAVIOR-CHANGE (complexity-optimizer): <what changed>.
// Before: <old behavior>. After: <new behavior>.
// Approved by the developer on <YYYY-MM-DD>. See OPTIMIZATION-REPORT.md item <ID>.
```

If the developer declines, keep the original behavior and use the best equivalent approach instead.

## NEEDS-TESTING marker

Rule 5: when the developer approves a change whose equivalence tests cannot fully verify, mark it in the code directly above the changed code, using the language's comment syntax:

```
// NEEDS-TESTING (complexity-optimizer): <what changed>.
// Unverified: <the exact behavior tests could not verify>.
// Approved by the developer on <YYYY-MM-DD>. See OPTIMIZATION-REPORT.md item <ID>.
```

Also list every marked change in a "Needs testing" section at the top of `OPTIMIZATION-REPORT.md`, with location, what is unverified, and a suggested way to verify it (manual test steps, an integration test, a staging check). Never remove a marker unless the developer confirms the behavior has been verified.

## Final summary

End every run with a short summary in the conversation:

- Items applied and verified, with the verification level and a one-line summary of the evidence for each.
- Items applied with developer approval but marked `NEEDS-TESTING`.
- Items applied with developer approval that knowingly change behavior (`BEHAVIOR-CHANGE`).
- Behavior changes still awaiting developer review.
- Items proposed but not applied.
- Bugs found (count and IDs).
- Dependency requests pending.
- Test suite status before and after, from runs on the final code, including tests that were already failing before analysis.
- Commits made (one per item) if the developer authorized them; otherwise, that nothing was committed and where the per-item list of changed files is.
- Parts of the requested scope that were not inspected.
- Items whose reachability is unknown, with the question for the developer about each: is this code used?
- Which performance numbers are measured and which are estimated, predictions that the measurements contradicted, and any verification that could not be completed.
- Changes tried and rejected.
- For a language without a companion file: the saved profile's path and what changed in it this session, with the reminder to commit it (later sessions load it instead of rebuilding it), or that it was not saved.
- Regression guards left in place (benchmarks or tests the developer chose to keep), and how to run them.
