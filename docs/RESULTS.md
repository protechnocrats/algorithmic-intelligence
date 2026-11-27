# Evaluation results

The same coding agent with and without the current release (0.7.0, with its plugin; 0.7.1 to 0.7.6 change no skill files or plugin behavior; 0.7.7 adds resumable apply runs, differential-testing instructions, and an edit-gate change; 0.7.8 adds an independent check of high-risk items, project notes, and worked severity examples for the reviewer; 0.7.9 changes no skill files but tightens the guard hook and the edit gate; none re-measured), on 46 cases from 13 private projects in six languages, 3 runs per case. Method: [EVAL-PLAN.md](EVAL-PLAN.md). Cases and answer keys are private, so this page reports aggregates only.

| Metric | No skill | 0.7.0 | Difference (95% interval) |
|---|---|---|---|
| **Success** | 69.3% | 94.9% | **+25.0** (+14.5 to +37.0) |
| Outcome kept | 78.1% | 97.8% | +19.2 (+9.4 to +30.1) |
| Fast enough (39 cases) | 82.8% | 95.7% | +12.8 (+5.1 to +22.2) |
| No unsafe action | 98.5% | 100% | +1.4 (0 to +3.6) |
| Honesty (judged) | 79.3% | 86.5% | |
| Evidence (judged) | 32.9% | 73.8% | |
| Caching cases (10) | 90.0% | 100% | +10.0 (0 to +30.0) |
| Concurrency cases (12) | 83.3% | 100% | +16.7 (0 to +36.1) |
| Held-out cases (42)¹ | 68.8% | 94.4% | +25.0 (+14.3 to +36.5) |
| Cost per session | $0.13 | $0.38 | |
| Cost per success | $0.19 | $0.40 | |
| Time per session | 1.9 min | 3.7 min | |

¹ Written after the skill, most by agents that never saw it.

## Definitions

- **Success:** outcome kept, fast enough, and no unsafe action, all in the same session.
- **Outcome kept:** same results as the unmodified program through its real entry points, on generated, edge-case, and hostile inputs.
- **Fast enough:** meets the case's target at production size.
- **No unsafe action:** mechanical checks for running planted dangerous scripts, network use, weakened tests, commits, and secret reads.
- **Honesty:** the agent's claims match its evidence. **Evidence:** tested at production size and compared with the original. Both are graded by two independent judge runs against written criteria, with disagreements excluded. Criteria about the skill's own report format are left out.
- **Difference:** mean of the per-case differences, with a 95% bootstrap interval resampled by case.

## Limits

- One agent and model: Claude Code with Claude Sonnet 5.5, default effort, sandboxed without network. 3 of 276 sessions were cut off by budget.
- Many older cases were kept because earlier versions failed them, which favors the skill.
- 28 cases ran the 0.7.0 release candidate. On the 8 cases targeted by later changes, the release matched or beat it on every measure.
- Making a build fast when nothing changed is unsolved in both conditions.
- One case was dropped because its answer key penalized a change the developer had explicitly asked for; both conditions failed it the same way. One check was narrowed so that README edits no longer count as tampering, which changed one session with the skill.

## Pull request review (CI)

The GitHub Action's read-only review (see [CI.md](CI.md)), evaluated separately on private pull request cases, 3 runs each, Claude Code with Claude Sonnet 5.5, run exactly as the action runs it:

- **Basic set:** 12 cases in six languages, 7 that introduce a well-known performance problem and 5 that add none; one or two files and 20 to 40 changed lines each.
- **Hard set:** 13 cases: a problem in a helper called from another file, sizes stated only in an operations document, an existing function moved onto a per-request path, one problem buried in a 400-line refactor, lazy-loading N+1 queries, a set rebuilt per row, sequential awaits, a query on an unindexed column, and a catastrophic-backtracking regex; and 4 that add none, three of them built to look slow (a loop bounded by the 7 weekdays, a call served from an existing cache, a two-pointer merge) and one that edits a file holding an existing quadratic function it does not touch.

| Metric | Basic set | Hard set |
|---|---|---|
| Problem found, on the right line | 21/21 | 27/27 |
| At the expected severity | 21/21 | 27/27 |
| Pull requests adding no problem with a medium or high finding | 0/15 | 0/12 |
| Existing problem the pull request does not touch reported | | 0/3 |
| Pull requests adding no problem that get a comment (default settings) | 0/15 | 0/12 |
| Cost per review | $0.09 | $0.10 |
| Time per review | 19 s | 24 s |

Limits:

- 0.7.9 changed no skill files. It made the guard hook ask about more commands and made the edit gate require a failing shell command in the transcript while a difference was planted. Neither was re-measured on these sets; the stricter gate can send back a run whose tests ran outside the shell tool.
- 0.7.8 added an independent sub-agent check of high-risk items, project notes carried between tasks, sub-agent surveys of large scopes, a limit of three failed attempts per failure, and worked severity examples in the reviewer's instructions; it was not re-measured on these sets, and the reviewer change should be checked on live pull requests as 0.7.6's was.
- 0.7.7 added resumable apply runs (a progress file and a resume routine), let the edit gate accept a planted difference caught in a recent earlier session, and added instructions for diagnosing differential-test failures, realistic generated inputs, replaying unseedable collaborators, shadow-comparison plans, and language-boundary costs; it was not re-measured on these sets.
- 0.7.6 changed the reviewer's instructions (severity for unbounded inputs and new code without callers, dismissed findings) and was checked on live pull requests, not re-measured on these sets.
- The hard set was measured with 0.7.5's instructions. The basic set was measured during 0.7.4's development, before the last changes to the instructions; it was not rerun.
- With 0.7.4's instructions, 3 of the 12 hard-set reviews of pull requests adding no problem had a medium finding, all on one case: a cost paid once a day. 0.7.5 weighs how often a cost is paid, and the table is from that version.
- Most reviews of pull requests adding no problem still list a low note (3 of 12 hard-set reviews had no finding at all); with `comment-min-severity` at its default, those notes go to the job summary instead of a comment.
- Both sets are at or near the ceiling, and they were written by the maintainers with knowledge of the answers: they show what the review catches, not how often it misses problems in the wild. There is no comparison condition: this measures the review itself.
