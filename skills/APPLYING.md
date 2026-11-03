# Applying

Apply mode only: Phases 5 and 6, after Phases 1 to 4 in `WORKFLOW.md`. Read this file together with `WORKFLOW.md`, in the same step. The mandatory rules and their full text ("Rule details" in `WORKFLOW.md`) apply throughout.

## Phase 5: Apply

For each approved item, one at a time:

1. **Characterize the original.** Write differential tests per `DIFFERENTIAL-TESTING.md`, with the original implementation copied verbatim as the reference, and turn the contract into executable checks ("The contract as executable properties"). Run them against the unchanged code first: they must pass, which shows the harness is wired correctly. Then check the check: the tests must catch planted differences, and pass with the original on both sides when behavior can vary between runs ("Check the check" in `DIFFERENTIAL-TESTING.md`). Keep one differential-test file and one benchmark program for the whole apply phase, and add each item to them ("Work in few, large steps" in `SKILL.md`).
2. **Change the code.** Make the smallest change that implements the chosen approach. Keep the signature and contract. Add a short comment where the technique is not obvious.
3. **Verify.** Run the differential tests and contract checks, then the full existing suite, then any bounded or exhaustive check from the verification plan. Walk the behavior traps again for this change, and confirm each is covered by a test or ruled out by analysis. Record the level reached.
4. **Benchmark.** Measure time and memory for the original and the new version at realistic `n`, at a larger `n`, and on worst-case inputs where relevant (`BENCHMARKING.md`). State the end-to-end effect: the share of the whole operation's time the changed code took before the change, and the resulting saving, measured where possible ("Component and end-to-end" in `BENCHMARKING.md`). Record the numbers as measured, with the measured growth exponent, and compare them with the Phase 3 prediction (`WORKFLOW.md`). If they disagree, find out why before keeping it: a wrong prediction means the analysis missed a cost. If the new version is not faster at realistic sizes, do not keep it unless the developer agrees for scaling reasons; a change not kept goes under "Tried and rejected." If verification or benchmarking cannot be completed, say so, report the gain as estimated only, and do not present the change as a confirmed win.
5. **Handle unverified parts and behavior changes.** If any behavior cannot be verified, or the change alters behavior in any way, stop work on this item: restore its original code, do not commit it, add it to "Behavior changes for review," and go on to the next item. Ask about every such item at the end; an earlier "apply all" does not approve it (rule 5). If the developer approves it, apply it with the `NEEDS-TESTING` or `BEHAVIOR-CHANGE` marker ("Code markers" below). If the developer declines it, apply the version that keeps the behavior, if one exists, through steps 1 to 4 ("Declined is not the end of the item" under rule 5 in "Rule details" in `WORKFLOW.md`).
6. **Run again after the final edit.** If anything changed after the last test run (review fixes, comments, formatting), run the differential tests and the full suite again. Results from an earlier version of the code do not count.
7. **Commit, only if authorized.** If the developer authorized commits (Phase 1, step 4, in `WORKFLOW.md`), make one commit per optimization, with a message that states the complexity before and after, the benchmark result, the verification level, and the tests added. Do not mix bug fixes, formatting, or unrelated refactors into it. Without authorization, do not commit: record in the report the exact files and functions this item changed, so the developer can review, commit, or revert it on its own.

If a differential test fails, the optimization is wrong: fix the optimization, never the test. If the failure shows that the original behavior is itself a bug, record it in the bug log and follow rule 4: if the best optimization removes the bug as a side effect, confirm that outputs differ only on inputs that trigger the bug and document it; otherwise keep matching the original.

## Phase 6: Close out

Write `APPLY-RESULTS.md` once, in one pass ("Apply results format" below), and leave `OPTIMIZATION-REPORT.md` exactly as the analysis wrote it. Cover what was applied, skipped, or rejected; final benchmark numbers against the predictions; changes tried and rejected while applying; bugs found while applying; and the full lists of `NEEDS-TESTING` and `BEHAVIOR-CHANGE` items. State plainly which items were verified and at which level (with the evidence), which the developer accepted with unverified behavior, and which knowingly change behavior. Call an item proven only at verification level 4. Offer to keep each item's benchmark as a regression guard ("Offer a regression guard" in `BENCHMARKING.md`), and list the ones the developer kept.

## Apply results format

`APPLY-RESULTS.md` (or, for a small result, the summary in the conversation) starts with the test suite status before and after (from runs on the final code), and the input sizes used with their sources and any disagreement between sources, then one entry per item the developer approved, using its ID from `OPTIMIZATION-REPORT.md`:

```markdown
### <ID>. <Short title> — <Applied (verified: level) | Applied (NEEDS-TESTING, developer approved) | Applied (BEHAVIOR-CHANGE, developer approved) | Not applied (reason; original restored)>

- **Complexity:** before → after in every size variable (for example O(n·k) → O(n), not only O(n²) → O(n)), with the case labeled (rule 9); the lower bound with its reason and basis, or "unknown" with why; and whether the new version reaches it.
- **Verification:** Level reached (tested | property-checked | exhaustively checked, with the domain | proven, with the tool and what it proved); inputs and properties covered (edge cases, generated cases, seeds, sizes); the planted differences the tests caught and the A/A result ("Check the check" in `DIFFERENTIAL-TESTING.md`); tests and tools actually run, with results; behavior left unverified. "Proven" only at that level.
- **Performance:** Measured time and memory before and after at realistic n, at a larger n, and on worst-case inputs where relevant, with environment, run count, median, and spread, as absolute values and percentage change; the measured growth exponent against the prediction, and the explanation when they disagree. If measurement could not be completed, say why; the item is not a confirmed win.
- **End-to-end:** The share of the whole operation's time (the request, job, frame, or command) the changed code took before the change, and the resulting saving for that operation, each labeled measured or estimated (rule 8). When it cannot be measured here, estimate it from the call frequency and sizes found in the survey, and say so. Never leave this field out.
- **Reproduce:** The commands, seeds, input generators, and environment needed to rerun the tests and benchmarks. When one harness covers several items, give these once in a "Reproduce" section at the end of the file and write "see Reproduce" here, with this item's own seeds or arguments if it has any.
- **Changed files:** The exact files and functions this item changed, and the commit if commits were authorized. Without commits, this list is how the developer reviews, commits, or reverts each item on its own.
```

Then these sections, each only if it has entries: "Needs testing" (see the marker below), "Behavior changes decided" (each item's decision, and any new behavior change found while applying, in the format under "Behavior changes for review"), "Tried and rejected while applying," and "Bugs found while applying" (in the bug log format).

## Code markers

**Known behavior change.** When the developer approves an item under "Behavior changes for review" (`REPORTING.md`), mark the code directly above the change, using the language's comment syntax:

```
// BEHAVIOR-CHANGE (algorithmic-intelligence): <what changed>.
// Before: <old behavior>. After: <new behavior>.
// Approved by the developer on <YYYY-MM-DD>. See OPTIMIZATION-REPORT.md item <ID>.
```

If the developer declines, apply the version that keeps the behavior, if one exists ("Declined is not the end of the item" under rule 5 in "Rule details" in `WORKFLOW.md`); otherwise leave the code unchanged.

**Unverified equivalence.** When the developer approves a change whose equivalence tests cannot fully verify (rule 5), mark the code directly above the change:

```
// NEEDS-TESTING (algorithmic-intelligence): <what changed>.
// Unverified: <the exact behavior tests could not verify>.
// Approved by the developer on <YYYY-MM-DD>. See OPTIMIZATION-REPORT.md item <ID>.
```

Also list every marked change in a "Needs testing" section of `APPLY-RESULTS.md`, with location, what is unverified, and a suggested way to verify it (manual test steps, an integration test, a staging check). Never remove a marker unless the developer confirms the behavior has been verified.
