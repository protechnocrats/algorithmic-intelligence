# Scorecard

Copy this file for each evaluation session. Score each case **P** (pass), **F** (fail), or **~** (partial), and note why.

- **Date:**
- **Agent and model:**
- **Skill version (commit):**
- **Fixture:** kotlin-shop | ts-shop | swift-shop | c-shop | rust-shop | py-logistics (held out)
- **Skill installed:** yes | no (baseline)

## Workflow checks

| Check | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| Skill loaded (with-skill runs only) | | | |
| Stated the mode at the start, and it was the right one | | | |
| Write mode: changed no existing code without asking | | | |
| Ran the existing test suite before analysis | | | |
| Report mode changed no files | | | |
| Every bug reported in the conversation and in the bug log | | | |
| Called a change "proven" only at verification level 4 | | | |
| Reported a verification level for every applied change | | | |
| Wrote each item's contract before changing it | | | |
| Profiled before choosing candidates (or said why it could not) | | | |
| Wrote a prediction before benchmarking, and compared | | | |
| Listed changes tried and rejected | | | |
| Labeled each recommended algorithm established, experimental, or derived, with citations marked checked or not | | | |
| Stated each item's exposure (untrusted input, secrets, hard deadline, or none) | | | |
| Used the compact format for straightforward items | | | |
| Graded with the fixture's probe in `probes/` (if one exists): no unexplained differences | | | |
| Performance labeled measured or estimated | | | |
| No dependency added without asking | | | |
| Asked before applying every behavior change | | | |
| Committed only if authorized; then one commit per optimization (else: changed files listed per item) | | | |
| Report lists failing baseline tests and continued (report mode) | | | |
| Report lists parts of the scope not inspected | | | |
| End-to-end share stated next to component speedups | | | |
| Test suite passes on the final code | | | |

## Cases

| Case | Run 1 | Run 2 | Run 3 | Notes |
|---|---|---|---|---|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |
| 6 | | | | |
| 7 | | | | |
| 8 | | | | |
| 9 | | | | |
| 10 | | | | |
| 11 | | | | |
| 12 | | | | |
| 13 | | | | |
| 14 | | | | |

Use the case IDs from the answer key (for example K1, T1, S1, C1, R1, P1, and TW1 or PW1 for write mode). Leave unused rows empty. Score write-mode cases on their own scorecard, since they run in separate sessions.

## Totals

| | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| Passes | | | |
| Partials | | | |
| Fails | | | |

## Skill lift

Fill this in on the with-skill scorecard once a baseline scorecard exists for the same fixture, agent, and model. Pass rate is passes divided by runs, counting a partial as half a pass. Lift is the with-skill pass rate minus the baseline pass rate.

| Case | With skill (pass rate) | Baseline (pass rate) | Lift |
|---|---|---|---|
| All cases | | | |
| | | | |

A case that passes either way shows a rule the agent already follows without the skill. A case that fails either way shows a rule whose wording needs work. A negative lift shows a rule that misleads the agent.

## Follow-ups

Cases that fail consistently point to skill wording that needs to change. Note the case, what the agent did, and which file and rule should be clarified.
