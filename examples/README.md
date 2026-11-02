# Examples

Real output from the skill, unedited, so you can see what it produces before installing it.

## `java-clinic-report/`: a report-and-apply run on a Java project

The files in [`java-clinic-report/`](java-clinic-report/) are what one agent session wrote on `evals/fixtures/java-clinic`, a small Java project with planted performance problems. The session ran Claude Code with Haiku 5.5 and the skill (round 6, 2026-11-01). It was asked "Find time complexity and data-structure problems in this project and write a report," then "Apply all the optimizations you recommend," and every approval it asked for was declined.

- [`OPTIMIZATION-REPORT.md`](java-clinic-report/OPTIMIZATION-REPORT.md): the analysis, written once before any change: each item's contract, current cost, lower bound, candidates and why each lost, risks, and the behavior changes held for the developer's decision.
- [`APPLY-RESULTS.md`](java-clinic-report/APPLY-RESULTS.md): what was applied, how it was verified, and what was measured.
- [`BUGS-FOUND.md`](java-clinic-report/BUGS-FOUND.md): bugs noticed, documented and not fixed.

The grading probe found no behavior difference from the original in any of the 10 checked functions.

## One item, with and without the skill

`PartnerImport.repeatedVisits` finds the visits that appear more than once in an upload. The upload comes straight from a partner hospital's request body, so the sender controls its contents. The original compares every row with every other row: O(n²).

**Without the skill** (a baseline session, round 7), the agent counted rows in a `LinkedHashMap<VisitKey, Integer>`. That is O(n) on ordinary data, and the results are correct, so every test passes. But `VisitKey` is a record of two `long`s: its hash code is predictable, and because it is not `Comparable`, Java's hash map cannot fall back to its tree buckets. An uploader who sends colliding keys makes every insertion scan the whole bucket. On 60,000 colliding rows the "optimized" version took **12.0 s**, against **3.4 s** for the quadratic original.

**With the skill** (item OPT-1 in the report), the agent marked the input as untrusted, wrote the reason down, and chose differently:

> **Candidates:** … 2. `HashMap` counts plus ordered output: O(n) expected. **Rejected by exposure.** `VisitKey` is a record of two `long`s, so its hash is predictable and an uploader can craft collisions. `VisitKey` is not `Comparable`, so `HashMap` tree bins do not help …

It sorted row indices by the two fields and scanned runs of equal keys: O(n log n) in the worst case, whatever the uploader sends. On the same 60,000 colliding rows: **52 ms**. It also kept the original's exact output order and its behavior on `null` rows, and verified both against the original with differential tests.

Same model, same project, same prompt. The difference is the judgment the skill asks for: who controls the input, what the worst case is, and proof that nothing else changed.
