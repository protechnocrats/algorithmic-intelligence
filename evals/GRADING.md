# Grading

Every evaluation round is graded on **every category below, for every session, in both conditions** (with and without the skill), by `evals/grade.py`. A round is not reported on one category, and nothing is graded by hand that the script can grade. The result is a scorecard that has the same shape in every round, so rounds, models, agents, and skill versions can be compared.

```bash
python3 -I evals/grade.py <run directory> [more ...]                # automatic categories, free
python3 -I evals/grade.py --judge --judge-cap 3 <run directory> ...  # adds the judged categories (costs money)
```

A run directory is one `run-pilot.sh` output directory (it holds `progress.log` and `logs/`). `grade.py` writes `scorecard.json` and `scorecard.md` into each directory and prints a combined scorecard grouped by model and condition. The results file for the round copies the combined scorecard in full, then discusses it.

## Categories

**A** marks a check `grade.py` computes from the session's files. **J** marks a check made by the judge: a separate model session that reads the answer key, the session's reports, its replies, and its code changes, and answers against a fixed rubric (below). Judged checks run only with `--judge`.

### 0. Validity (gate)

A session that fails any of these is reported as invalid and left out of every other category.

| Check | How |
|---|---|
| Every turn finished, with no stall, usage-limit error, or skip | A: `progress.log` |
| Permission refusals below 10% of tool calls | A: transcripts |
| With the skill: the skill was loaded. Without: it was not | A: transcripts |

### 1. Behavior safety

| Check | How |
|---|---|
| Cases whose behavior differs from the original, per the probe | A: the fixture's probe (`probes/`) |
| The fixture's test suite passes on the final code | A: `logs/*.final` |
| Report mode changed no tracked file | A: `logs/*.after-report.status` |
| No dependency added | A: the build files compared with the initial commit |

### 2. Case outcomes

| Check | How |
|---|---|
| Each case scored **P**, **~**, or **F** against its answer key's "Pass" and "Fail" lines | J, given the probe's verdict for the case as evidence |
| Speed reached on each probed timing (original and final) | A: the probe's `time` and `info` lines |

### 3. Protocol

| Check | How |
|---|---|
| Stated the mode in the first reply | A: first reply text |
| Behavior changes listed for review and not applied on a general "apply all" | J (the probe shows whether one was applied) |
| Declined behavior changes: the version that keeps the behavior applied when one exists | J |
| No commit without authorization | A: `git log` in `logs/*.final` |
| Ran the existing test suite before analysis | A: transcript order |
| Every bug reported in the conversation and in the bug log | J |

### 4. Analysis quality

| Check | How |
|---|---|
| Contract written for each item | J |
| Lower bound stated with its basis, never invented | J |
| At least three candidates for nontrivial items | J |
| Exposure stated (untrusted input, secrets, deadline, or none), and the worst case used where it counts | J |
| Cost counted along the call chain, including built-in and library calls | J |

### 5. Verification quality

| Check | How |
|---|---|
| A verification level reported for every applied change | J |
| "Proven" used only for a machine-checked proof or a check of the whole domain | J |
| Check the check: planted differences caught, A/A run when behavior can vary | J |
| Calls into other systems verified against a fake of the documented contract | J |

### 6. Measurement quality

| Check | How |
|---|---|
| Prediction written before benchmarking, and compared with the measurement | J |
| Every performance claim labeled measured or estimated | J |
| End-to-end share stated next to each component speedup | J |

### 7. Report completeness

| Check | How |
|---|---|
| Every field the `REPORTING.md` templates require | A: `check-report.py` (with-skill sessions; a baseline has no required format) |
| `OPTIMIZATION-REPORT.md` written once, never rewritten in apply mode | A: transcript |

### 8. Skill use (with-skill sessions)

| Check | How |
|---|---|
| Skill files read: `WORKFLOW.md` or `WRITING-NEW-CODE.md`, `DIFFERENTIAL-TESTING.md`, `REPORTING.md` | A: transcript |

### 9. Cost and efficiency

| Check | How |
|---|---|
| Reported cost, agent turns, input and output tokens, wall time | A: transcripts, `progress.log` |
| Cost by activity (reading, harness writing and running, reports, commits) | A: `cost-breakdown.py` |

## The judge

The judge is a model, so it is checked like any other test ("check the check"):

- **One rubric, fixed per round.** The prompt is built by `grade.py` from the answer key and the J rows above, never written by hand per round. The judge must quote the evidence (a line from a report or reply) for every score; a score without evidence counts as unscored.
- **Blind to the condition.** The judge is not told whether the session had the skill. Skill-specific file names stay in the evidence, so blinding is partial; say so in results.
- **Validated before use.** Before a judge model is used for a round, run it on a session with a planted defect (`grade.py --judge-selftest`: the report with one required analysis removed) and confirm it scores that check as failed.
- **Default model:** the one given by `--judge-model` (default `claude-sonnet-5-5`). Record the model in the results file. Changing it changes the scores, so keep it fixed across rounds that are compared.

## Reading the scorecard

- **Compare conditions within a model.** The skill's effect is the difference between conditions on the same fixture, model, and agent, with the number of sessions behind each number.
- **Every category is reported, including the ones where the skill loses** (cost, speedups held back).
- **Small samples:** report counts ("4 of 5"), not percentages alone, and do not call a difference of one session a result.
