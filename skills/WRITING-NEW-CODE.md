# Writing New Code

Write mode: the developer asked for new code (a feature, module, function, endpoint, script, or migration). The aim is code that is efficient from the start, so it never needs a later optimization pass. Writing the obvious nested loop or per-item query and planning to fix it later is the failure this mode exists to prevent; the opposite failure is custom structures, caches, parallelism, or dependencies for data that is small and cold.

The request defines what the code does; this file governs only how: algorithms, data structures, and hidden costs. It adds no features and does not turn a feature request into an optimization report. The only approvals new code needs are the ones `SKILL.md` always requires: a new dependency, semantics or security weaker than the request implies, a schema, migration, index, or configuration change the request does not name, and a commit.

**Contents:** New code and existing code · Which rules apply · Designing the code · When existing code is the bottleneck · Tests · Summary

## New code and existing code

New code is anything written during this task, including your own earlier drafts; revise it freely. Existing code was there before the task began, committed or not; change it only as far as the request requires. Changing existing code because it is slow is apply mode and needs the developer's agreement ("When existing code is the bottleneck").

## Which rules apply

The mandatory rules in `SKILL.md` apply as written, with these differences for new code. Where the work changes existing code, rules 3 to 5 and 12 apply to that code in full ("Rule details" in `WORKFLOW.md`).

| Rule | In write mode |
|---|---|
| 3. Understand and verify | New code has no original, so it gets a reference version and executable contract checks instead (see "Tests"), and a reported verification level |
| 4. Bugs reported, not fixed | Applies to existing code outside the request. If the request is a bug fix, that fix is the task |
| 5. No silent behavior changes | Decide before writing: if the planned design is weaker than the request implies (approximate results, a different order, eventual consistency, merged duplicates, possibly stale results), write the version that keeps the semantics and offer the faster one as an option. For a cache, that means one that sees every writer's changes, or no cache |
| 6. Best complexity | Reach the best bound for the workload the code will actually see; build nothing for workloads it will not. Compare approaches only where the choice is not obvious |
| 8. Measure | Estimate sizes before choosing. Benchmark only when two candidates are close or the developer gave a performance requirement (`BENCHMARKING.md`), prediction first. Label every claim measured or estimated |
| 10. Beyond CPU loops | Batch database, network, and I/O access from the first version |
| 11. Public contract | Holds for existing public APIs; new APIs follow the request |
| 12. Start green | Only when existing code changes. A new project without tests skips it |

## Designing the code

**Language first.** Read the language file before designing, even for one small function: its "Hidden costs" section is where most write-mode inefficiency comes from. For a language without a file, `languages/GENERIC.md` covers the saved profile; that profile is the one file outside the request write mode may create or update, and only with the developer's permission.

**Size the work.** The request is often a known problem in disguise ("tell dispatchers when…", "find customers who…"); name it during "Translate the request" in `SKILL.md`. For every part that loops over data, queries a store, or runs per item, request, or frame, write down the input sizes, how they grow, how often the code runs, and where each number came from (request, existing code, configuration, or estimate). "Estimate before building" in `DISCOVERY.md` (move 11) covers conflicting sources and sizes nobody can give; ask one short question only when a size decides the design and cannot be estimated. Note the exposure as in Phase 2 of `WORKFLOW.md`: untrusted input, secrets, or a hard deadline means choosing by the worst case with `techniques/hostile-inputs.md`.

**Spend effort where it matters.** Code whose inputs are provably small and that does not run hot (both defined under rule 8 in "Rule details" in `WORKFLOW.md`) gets the simplest clear implementation and no summary entry. The rest gets the design below.

**Choose the approach.** Count every call at its real cost, built-ins, library calls, and existing code included (rule 6). State the work as an abstract problem and use `ALGORITHM-ARSENAL.md` and the `CORE-TECHNIQUES.md` sections it routes to, checking each technique's "Valid when" column against the data. When nothing fits, derive an approach with `DISCOVERY.md` rather than falling back to the nested loop.

When input comes from users or other systems, the design holds under hostile input from the start, because retrofitting a limit later changes the contract: validate before expensive work, bound sizes, counts, and nesting depth, choose worst-case structures or keyed hashing for attacker-chosen keys, and key caches by user, tenant, and permissions. `techniques/hostile-inputs.md` and "Security-sensitive behavior" in `BEHAVIOR-TRAPS.md` have the specifics. None of these is traded for speed without the developer approving that specific trade ("When the request itself is risky" in `SKILL.md`).

**Account for existing code you call.** Calling an existing function in a loop multiplies its cost by the loop count ("Cost along the call chain" in `WORKFLOW.md`), and that cost belongs to your design. Call slow code once per distinct input, or once before the loop. Reusing results within one call of your code is safe when nothing can change them during that call; prefer that scope. A cache that outlives a call needs a size bound (rule 1), invalidation for every input it depends on including writes from other processes and jobs, and a key covering every input that changes the result ("Caching traps" and "Security-sensitive behavior" in `BEHAVIOR-TRAPS.md`). Before caching a result, read what each caller does with it: if any caller mutates or keeps it, hand out copies or cache only the inputs ("Mutation and aliasing" in `BEHAVIOR-TRAPS.md`).

**Comment the non-obvious.** Name the algorithm or structure, its complexity, and the assumption behind it, so the next reader can tell when it has gone stale:

```
// Index by SKU once: O(n + m) instead of O(n·m); assumes the catalog fits in memory (about 50,000 SKUs).
```

## When existing code is the bottleneck

Sometimes the best new code is still slow because of existing code it must call (a linear lookup behind a private field, a query with no index). Minimize calls into it, leave it unchanged, report it in the summary in the report-mode item format from `REPORTING.md` (location, cost along the call chain from the new code, recommended fix), and ask whether the developer wants it optimized. If so, that item follows apply mode, with differential tests against the existing code.

## Tests

- **Reference version.** For each part that got a real design, write a slow, obviously correct version in test code (usually the loop you chose not to ship) and compare against it on edge cases and generated inputs, as `DIFFERENTIAL-TESTING.md` compares old and new code. This gives new code the same evidence a change to existing code gets.
- **Contract checks.** Assert the request's postconditions on every generated case, and the invariant of any derived algorithm. Where no simple reference exists, use metamorphic relations ("The contract as executable properties" in `DIFFERENTIAL-TESTING.md`).
- **Verification level.** Aim for the highest cheap level ("Verification levels" in `DIFFERENTIAL-TESTING.md`); exhaustive checks over a small domain are often cheap for new code.
- **Round trips.** When new code reads what existing code writes, or the reverse, test the round trip on generated data that includes every special case the existing code handles (quoting, escaping, separators and line breaks inside values).
- **Realistic size.** Where a design choice was made for performance, run one correctness test at the realistic size. Assert on correctness, not timing; timing assertions are flaky.
- **Concurrent callers.** Shared state the new code adds (a cache, an index, a counter) gets a test with concurrent callers, under the race detector or thread sanitizer where one exists.
- **Own structures.** A structure written in the project gets its own tests ("Testing a new data structure" in `DIFFERENTIAL-TESTING.md`).
- Existing tests are evidence: a test edited, skipped, or deleted to make the work pass proves nothing. Report only tests that actually ran.

## Summary

End with the normal summary of the work, then a short **Performance decisions** list. Open it with "Request as understood" in a line or two. Then one entry per designed part (small, cold code gets none):

```
- <location>: <what it does>
  Size: <assumption> (<source>; <conflicting source and number, if any>)
  Approach: <choice>, over <rejected alternative> because <reason> [derived]
  Memory: <bound and bytes across all copies, vs. the limit compared with>   (caches, memo tables, indexes only)
  Verified: <level> against <reference version | contract checks>
```

After the entries, list as applicable: bottlenecks in existing code, as proposed items awaiting a decision; dependencies you would have used but did not; which claims are measured and which estimated.

Close with the lines from "Every final summary" in `SKILL.md`: Complexity (per designed part, time and space, case labeled, lower bound or "unknown, because …"), Bugs noticed, Hazards noticed, Commands not run, and Waiting for approval.
