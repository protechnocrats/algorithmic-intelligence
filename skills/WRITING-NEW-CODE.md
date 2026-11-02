# Writing New Code

Use this file in write mode: the developer asked for new code (a project, feature, module, function, endpoint, script, or migration) and the skill is loaded. The goal is code that is efficient from the start, so it never needs an optimization pass later.

The developer's request defines what the code does. This file only governs how it does it: which algorithms and data structures to use, and how to avoid hidden costs. It never adds features, changes requirements, or slows the task down with reports and approval steps for new code.

## New code and existing code

Every line the work touches is one of two kinds. Decide which before writing.

- **New code:** code that did not exist before the current task, including code you wrote earlier in this same task. Write and revise it freely.
- **Existing code:** code that existed before the current task started, whether committed or not. Change it only as far as the developer's request requires. Never change existing code just to make it faster: that is apply mode, and it needs the developer's request or approval (see "When existing code is the bottleneck").

## Which rules apply

The mandatory rules in `SKILL.md` apply as follows. "As written" means exactly as in report and apply mode.

| Rule | In write mode |
|---|---|
| 1. Time is invaluable, space bounded | As written. Every cache, memo table, or index in new code has an explicit bound and fits any memory budget the project has, counted across every copy that can exist at once (per process, worker, request, or tenant) |
| 2. Time first, then space | As written |
| 3. Understand and verify | For existing code you change because the request requires it: understand it first, and keep the existing test suite passing. New code has no original to compare against, so it gets a reference version written for the tests instead, plus executable checks of its contract, and a reported verification level (see "Tests") |
| 4. Bugs documented, never fixed on purpose | For bugs you notice in existing code outside the request: document them and tell the developer, do not fix them. If the request is itself a bug fix, fixing that bug is the task |
| 5. Behavior changes never silent | For existing code: as written. For new code: never choose weaker semantics than the request implies without asking. That means approximate instead of exact results, a different order than the request specifies or implies, eventual instead of immediate consistency, dropped or merged duplicates, or results that can be stale |
| 6. Best possible complexity | Reach the best bound for the workload the code will see (see "Steps"). Do not add machinery for workloads the code will never see. No candidate quota: compare approaches only where the choice is not obvious |
| 7. Data structures earn their place; dependencies need permission | As written |
| 8. Measure, do not only reason | Estimate sizes before choosing. Benchmark only when two candidates are close, or when the developer gave a performance requirement, and write the prediction before running the benchmark (`BENCHMARKING.md`). Label every performance claim as measured or estimated |
| 9. State which case you mean | As written, in comments and in the summary |
| 10. Look beyond CPU loops | As written: design database access, network calls, and I/O to be batched from the start |
| 11. Keep the public contract | As written for existing public APIs. New APIs follow the request |
| 12. Start green | Only when the work changes existing code: run the existing suite before and after, and if it already fails, report the failures and stop before changing existing code. A new project with no tests skips it |
| 13. Respect the project's idioms | As written |
| 14. Language's own structures first | As written |

## Steps

1. **Setup.** Start your reply by stating the mode in one line ("Write mode: …"; see "First, state the mode" in `SKILL.md`). Detect the language and version, and load the language companion file (`SKILL.md`, "Language detection"). Its "hidden costs" section lists the traps to avoid while writing. For a language without a companion file, load the profile saved in the project at `.algorithmic-intelligence/languages/<LANGUAGE>.md` if it exists; otherwise build one and ask whether to save it there, as `languages/GENERIC.md` describes. The saved profile is the one file outside the request that write mode may create or update, and only with that permission.
2. **Size the workload.** For every part of the new code that loops over data, queries a database or service, or runs per item, per request, or per frame, write down the expected input sizes, how they grow, and how often the code runs. Take them from the request, the existing code (limits, pagination, volume constants, schemas), or reasonable estimates, and state which. If a size decides the design and cannot be estimated at all, ask one short question; otherwise state your assumption and continue. Also note the exposure (`WORKFLOW.md`, Phase 2, step 7): untrusted input, secrets, or a hard deadline means choosing by worst case with `techniques/hostile-inputs.md`.
3. **Separate the parts that matter.** Code whose inputs are provably small and that does not run hot (rule 8 defines both) gets the simplest clear implementation. Everything else gets steps 4 to 6.
4. **Choose algorithms and structures.** When you estimate a design's cost, count every call it makes at its real cost, including built-in operations, library calls, and calls into existing code ("Count every call at its real cost" under rule 6 in `SKILL.md`): a short built-in call inside a loop is not free. Restate the work as an abstract problem, then use the six questions and the "Start from the current complexity" table in `ALGORITHM-ARSENAL.md`, then the sections of `CORE-TECHNIQUES.md` it points to (and `ADVANCED-TECHNIQUES.md` where its topics apply). Check each technique's "Valid when" column against the request and the data. When the right choice is obvious (a hash map instead of a repeated linear search), use it. When it is not, compare the plausible approaches briefly and pick one. When nothing in those files fits the problem (a custom rule or aggregate that no table names), use `DISCOVERY.md` to derive an approach instead of falling back to the obvious nested loop.
5. **Account for existing code you call.** Calling an existing function is part of your code's cost. If you call it inside a loop, multiply its cost by the loop count (WORKFLOW.md, Phase 2, "Cost along the call chain"). Structure the new code so it calls slow existing code as few times as possible: once per distinct input instead of once per item, or once before the loop instead of inside it. Reusing results within one call of your code is safe when nothing can change them during that call (no writes, no hidden inputs: see `BEHAVIOR-TRAPS.md`). A cache that outlives one call is allowed only with an explicit bound (rule 1) and invalidation for every input it depends on (`BEHAVIOR-TRAPS.md`, "Caching traps"); prefer the per-call scope whenever it is enough.
6. **Write it.** Follow the project's idioms and the language file. Add a short comment wherever the algorithm or structure is not obvious, naming it and its complexity (for example, `// Index by SKU once: O(n + m) instead of O(n·m)`).
7. **Test it.** See "Tests".
8. **Summarize.** See "Summary".

## When existing code is the bottleneck

Sometimes the best the new code can do is still slow because of existing code it must call (a linear lookup inside a class whose data is private, a query without an index). Then:

1. Write the new code to minimize calls into the slow code (step 5). Do not change the slow existing code.
2. Report the bottleneck in the summary using the report-mode item format from `REPORTING.md`: location, cost along the call chain from your new code, and the recommended fix.
3. Ask whether the developer wants it optimized. If they agree, that item follows apply mode, with differential tests against the existing code.

## Tests

- Test the behavior the request specifies, including edge cases: empty input, one element, duplicates, ties, and invalid input the code can receive.
- Where a design choice exists for performance, add at least one test with input at the realistic size from step 2. The test checks correctness on that input and must finish in reasonable time. Do not assert on timing; timing assertions are flaky.
- **Reference version.** For every part that steps 4 to 6 covered, write a slow, obviously correct version in test code, usually the straightforward loop you chose not to ship, and compare the shipped code against it on edge cases and generated inputs, exactly as a differential test compares old and new code (`DIFFERENTIAL-TESTING.md`). This gives new code the same evidence that changes to existing code get.
- **Contract checks.** Check the request's postconditions on every generated case, and the invariant of any algorithm you derived (`DISCOVERY.md`, move 3). Where no simple reference is practical, check metamorphic relations instead ("The contract as executable properties" in `DIFFERENTIAL-TESTING.md`).
- **Verification level.** Aim for the highest cheap level from "Verification levels" in `DIFFERENTIAL-TESTING.md`. Exhaustive checks over a small domain often cost little for new code.
- Where the new code uses a structure written inside the project (a heap, a ring buffer), give the structure its own tests (`DIFFERENTIAL-TESTING.md`, "Testing a new data structure").
- Run the new tests, and the existing suite when existing code changed. Report only what actually ran.

## Summary

End with the developer's normal summary of the work, plus a short "Performance decisions" list. For each part of the new code that steps 4 to 6 covered:

- **Location** and what it does.
- **Size assumption** and its source (request, existing code, or estimate).
- **Complexity** in time and space, with the case labeled (rule 9).
- **Why this approach,** and the alternative you rejected when the choice was not obvious. Mark an approach you derived rather than took from a known technique.
- **Verification level** reached against the reference version or the contract checks.

Then list:

- Any bottleneck in existing code (see "When existing code is the bottleneck"), as a proposed item awaiting the developer's decision.
- Bugs noticed in existing code (rule 4).
- Dependencies you would have used and did not, because they need permission (rule 7).
- Which performance claims are measured and which are estimated.

Keep the list short. Parts of the code that are small and cold do not need entries.

## Anti-patterns in write mode

1. Writing the obvious nested loop, linear lookup in a loop, or per-item query, then planning to optimize later.
2. Over-engineering: custom structures, caches, parallelism, or dependencies for data that is small and cold.
3. Changing existing code for speed during a feature task, without the developer's request or approval.
4. Hiding the cost of existing code by calling it inside a loop and analyzing only the new code.
5. Choosing approximate, reordered, or possibly stale results that the request did not allow.
6. A cache in new code with no bound, no invalidation, or a scope wider than the data it holds.
7. Turning the developer's feature request into an optimization report.
