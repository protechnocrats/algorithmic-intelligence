# Reporting

## Where reports go

For a small result (one or two items), present the report in the conversation. Otherwise ask the developer where to write it, suggesting `optimization-report/` at the project root, and ask whether it should be ignored by version control. Each phase writes its own files, once:

- `OPTIMIZATION-REPORT.md` — written in Phase 4: the ranked items, behavior changes for review, and tried-and-rejected candidates from the analysis.
- `BUGS-FOUND.md` — written in Phase 4: every bug noticed during the analysis. None are fixed on purpose.
- `APPLY-RESULTS.md` — written at the end of apply mode (Phase 6): what was applied and how it was verified and measured, changes marked as needing testing, behavior changes decided, changes tried and rejected while applying, and bugs found while applying. It refers to items by the IDs in `OPTIMIZATION-REPORT.md`.

**Write each file once, and do not edit it afterward.** Text an agent writes stays in the conversation, and every later step sends the whole conversation to the model again, so a report's size is paid for again on every step after it is written, and every edit adds another copy of the changed text. Keep findings in your working notes as you analyze; write `OPTIMIZATION-REPORT.md` and `BUGS-FOUND.md` once, after Phase 3 is complete for every candidate. In apply mode, never edit or rewrite `OPTIMIZATION-REPORT.md`: the developer is deciding from it, and its analysis must stay as written. Record each item's results in your notes and write `APPLY-RESULTS.md` once, at close-out. If you find a mistake in a file you already wrote, fix it in one combined edit and say what changed. If the developer asks for progress before then, answer in the conversation.

**Keep each file as short as the decisions allow.** Every field below appears, but in one line unless the item needs more: no narrative, and each fact stated once (refer to the item or section that already says it). An item may expand a field into short sub-bullets only when the developer has to decide something about it: an item under "Behavior changes for review," unverified equivalence, an exposure (untrusted input, secrets, a hard deadline), or a new dependency.

## Report header

Start `OPTIMIZATION-REPORT.md` (or the in-conversation report) with these sections, before any items:

- **Test suite baseline:** pass and fail counts from the run before analysis. If any tests failed, list them by name, and say which items they could affect (rule 12). In report mode the analysis continued despite them; in apply mode nothing was changed until the developer decided.
- **Scope:** what the developer asked to cover; what was inspected; and every part of that scope that was **not** inspected (modules, directories, languages, generated code), with the reason (size, time, no access, toolchain missing). Write "Everything in scope was inspected" only when that is true. Code outside the scope that was read only to trace a cost along the call chain is listed separately.
- **Language profile** (only for a language without a companion file in the skill): whether a profile saved in the project was loaded (its path and recorded version) or one was built in this session; whether it was saved or updated, at which path, and how many claims are still unverified. If the developer did not allow saving it, include the profile here in full, so the facts the analysis relied on are visible.

## Optimization item format

Rank items by expected real-world impact. Use the full format for nontrivial items (rule 6) and for any item with behavior risks or an exposure; straightforward items and items not worth changing use the compact format. The format marks the difficulty: full format means nontrivial, compact means straightforward or not worth changing.

Compact format:

```markdown
### <ID>. <Short title>

- **Where:** `path/to/File.kt:123` — `functionName`; reached from <entry point and how often>.
- **Contract:** What it returns and changes, in one line.
- **Now → recommended:** O(...) → O(...) [case], at the lower bound because ...; or "not worth changing" with the size bound and why the path is cold (rule 8).
- **Evidence and verification:** Bottleneck evidence (profile, measurement, or estimate); planned verification level.
- **Status:** As in the full format.
```

Full format, one line per field unless the item needs more (see "Keep each file as short as the decisions allow"):

```markdown
### <ID>. <Short title>

- **Where:** `path/to/File.kt:123` — `functionName`. Reached from <entry point: route, job, listener, command, UI handler, public API> <how often>; or "tests only"; or "unknown: no entry point found" with the places searched (dependency-injection configuration, scanning, plugin registries, routes, reflection) and the question for the developer: is this code used? Callers, thread, and input sizes (typical and maximum, with the source of the assumption).
- **Contract:** Requires (preconditions); returns (including order, ties, and duplicates); changes, throws, or calls (effects). Mark anything inferred rather than shown by the code and its callers.
- **Cost now:** Time O(...) [worst | average | expected | amortized], space O(...), in named variables, including the functions it calls and the total along the call chain when callers loop. Bottleneck: CPU | memory | I/O | network | lock | queue, with the evidence (profile, trace, query plan, benchmark, developer report, or static estimate only).
- **Lower bound:** Ω(...) because ...; basis: proven | conditional (state the assumption) | conjectured | workload-dependent | unknown (the reason, and the strongest bound you can support). Never invent a bound (rule 6).
- **Candidates:** At least three for a nontrivial item, one line each: approach — time O(...) (preprocessing and per query separately), space O(...); found by (a table row, a `DISCOVERY.md` move, or a published source); provenance (established with its common name and a reference, experimental with its publication, or derived with its correctness argument); citation checked or not checked; and either "chosen" or why it lost. Also name candidates considered and dropped, with the reason.
- **Recommended:** The chosen approach, time O(...) [case], space O(...). Kind of win: asymptotic | constant-factor | work avoided (never present the last two as a complexity reduction). Why not better: at the lower bound, or what blocks the gap (a dependency, a call pattern that cannot amortize preprocessing, an unmet assumption, a measured constant factor), and the `DISCOVERY.md` moves tried when no table row reached the bound.
- **Assumptions and risks:** Each assumption the technique needs, with the evidence that it holds; each trap from `BEHAVIOR-TRAPS.md` that applies and how it will be covered. Behavior changes: none, or see "Behavior changes for review" <ID> (rule 5).
- **Exposure, memory, dependency:** Exposure: none, or untrusted input | secret-dependent | hard deadline with the worst-case bound and the defense (`techniques/hostile-inputs.md`). Memory: new memory per copy × copies that can exist at once (per process, worker, thread, connection, request, or tenant) = total, and why it is bounded (rule 1). Dependency: none, or the library, version, license, and why (requires the developer's permission).
- **Prediction and verification plan:** Written before any benchmark: the expected speedup at realistic n and the expected growth exponent of each version. The verification level planned (see "Verification levels" in `DIFFERENTIAL-TESTING.md`) and how it will be reached.
- **Status:** Proposed | Awaiting developer review | Not worth changing (n is small and the path is cold) | Skipped (reason).
```

## Apply results format

`APPLY-RESULTS.md` starts with the test suite status before and after (from runs on the final code), then one entry per item the developer approved, using its ID from `OPTIMIZATION-REPORT.md`:

```markdown
### <ID>. <Short title> — <Applied (verified: level) | Applied (NEEDS-TESTING, developer approved) | Applied (BEHAVIOR-CHANGE, developer approved) | Not applied (reason; original restored)>

- **Verification:** Level reached (tested | property-checked | exhaustively checked, with the domain | proven, with the tool and what it proved); inputs and properties covered (edge cases, generated cases, seeds, sizes); the planted differences the tests caught and the A/A result ("Check the check" in `DIFFERENTIAL-TESTING.md`); tests and tools actually run, with results; behavior left unverified. "Proven" only at that level.
- **Performance:** Measured time and memory before and after at realistic n, at a larger n, and on worst-case inputs where relevant, with environment, run count, median, and spread, as absolute values and percentage change; the measured growth exponent against the prediction, and the explanation when they disagree. End-to-end: the share of the whole operation's time the changed code took before the change, and the resulting end-to-end saving, each labeled measured or estimated (rule 8). If measurement could not be completed, say why; the item is not a confirmed win.
- **Reproduce:** The commands, seeds, input generators, and environment needed to rerun the tests and benchmarks.
- **Changed files:** The exact files and functions this item changed, and the commit if commits were authorized. Without commits, this list is how the developer reviews, commits, or reverts each item on its own.
```

Then these sections, each only if it has entries: "Needs testing" (see the marker below), "Behavior changes decided" (each item's decision, and any new behavior change found while applying, in the format under "Behavior changes for review"), "Tried and rejected while applying," and "Bugs found while applying" (in the bug log format).

## Tried and rejected

Negative results are findings: they stop the next person from repeating the attempt. Keep a "Tried and rejected" section for every change that was built or benchmarked and then not kept, in `OPTIMIZATION-REPORT.md` for the analysis and in `APPLY-RESULTS.md` for apply mode:

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

Rule 5: every optimization that would change observable behavior, including changes that look like improvements, is listed at the top of `OPTIMIZATION-REPORT.md` under "Behavior changes for review" before anything is applied (and in `APPLY-RESULTS.md` if found while applying):

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
// BEHAVIOR-CHANGE (algorithmic-intelligence): <what changed>.
// Before: <old behavior>. After: <new behavior>.
// Approved by the developer on <YYYY-MM-DD>. See OPTIMIZATION-REPORT.md item <ID>.
```

If the developer declines, keep the original behavior and use the best equivalent approach instead.

## NEEDS-TESTING marker

Rule 5: when the developer approves a change whose equivalence tests cannot fully verify, mark it in the code directly above the changed code, using the language's comment syntax:

```
// NEEDS-TESTING (algorithmic-intelligence): <what changed>.
// Unverified: <the exact behavior tests could not verify>.
// Approved by the developer on <YYYY-MM-DD>. See OPTIMIZATION-REPORT.md item <ID>.
```

Also list every marked change in a "Needs testing" section of `APPLY-RESULTS.md`, with location, what is unverified, and a suggested way to verify it (manual test steps, an integration test, a staging check). Never remove a marker unless the developer confirms the behavior has been verified.

## Final summary

End every run with a short summary in the conversation. When the report is in files, give each point below in a line or two and point to the files for the detail; do not restate them in the conversation, since the developer already has them. When the report itself is in the conversation, it carries these points and no separate summary is needed:

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
