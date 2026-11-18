# Evaluation results

The same coding agent with and without the current release (0.7.0, with its plugin; 0.7.1 to 0.7.4 change no skill files or plugin behavior), on 46 cases from 13 private projects in six languages, 3 runs per case. Method: [EVAL-PLAN.md](EVAL-PLAN.md). Cases and answer keys are private, so this page reports aggregates only.

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

The GitHub Action's read-only review (see [CI.md](CI.md)), evaluated separately: 12 private pull request cases in six languages, 7 that introduce a performance problem and 5 that add none, 3 runs each (36 reviews), Claude Code with Claude Sonnet 5.5, run exactly as the action runs it.

| Metric | 0.7.4 |
|---|---|
| Problem found, on the right line | 21/21 |
| At the expected severity | 21/21 |
| Clean pull requests with a medium or high finding | 0/15 |
| Clean pull requests with no finding at all | 13/15 |
| Cost per review | $0.09 |
| Time per review | 19 s |

Limits:

- The cases are small (one or two files, 20 to 40 changed lines) and the problems are well known, so both results sit at the ceiling: they show the review catches common problems without false alarms, not how it does on subtle ones.
- An earlier run of the same cases found that the reviewer gave line numbers from the diff file instead of the source file; 0.7.4 fixes this before release, and the table is from the fixed version. Some fixes made after this run, from a live test on a real pull request, were not measured here.
- Unlike the skill's evaluation above, there is no comparison condition: this measures the review itself.

