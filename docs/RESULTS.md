# Evaluation results: skill vs no skill

This page reports two evaluation rounds of the skill:
- the first full round, run on 2026-11-12 and 2026-11-13 against version 0.6.5, using the exact files that were later released;
- a second round on 2026-11-13 comparing version 0.6.6 with 0.6.5 and with no skill, on a new project neither version was developed against (see "Version 0.6.6").

It answers one question: when a coding agent is given the same request on the same project, does loading the skill make the result better, and never worse or less safe? And what does it cost?

The method is in [EVAL-PLAN.md](EVAL-PLAN.md). The test cases, fixtures, traps, and answer keys are private, so they stay held out and the skill cannot be tuned to them. This page reports aggregates only.

## Summary

From the 0.6.5 round:
- **The skill makes agents break things less often.**
  - With the skill, the program kept its exact outcome in 95% of sessions.
  - Without it, 77%.
- **It makes agents much safer.**
  - 1 session with the skill did something unsafe, against 13 without it.
  - Without the skill, 8 of those sessions wiped the project by running a project script that deletes files when a variable is unset.
- **It makes agents more honest about their evidence.**
  - Agents with the skill tested at production size and compared results with the original code far more often (81% vs 48%).
  - They labeled numbers as measured or estimated correctly more often (82% vs 67%).
- **It does not make code faster than the agent alone.** Both conditions reached the required speed at production size about equally often. The skill's value is in getting the speedup without changing what the program does.
- **It costs about twice as much per successful task:** $0.35 vs $0.17 in agent cost, and 3.4 vs 2.0 minutes per session.

From the 0.6.6 round:
- **The benefit carries over to a project the skill was never developed against.** On a new project written by agents that never saw the skill, 0.6.6 succeeded in 87% of sessions, 0.6.5 in 73%, and the agent without the skill in 63%.
- **0.6.6 is better than 0.6.5 there:** +13.3 points of success (+3.3 to +23.3), with no unsafe session in any condition.

## Headline

432 sessions: 72 cases, each run 3 times with the skill and 3 times without it. A session succeeds only if all three checks pass:
- the program's outcome is unchanged;
- it is fast enough at production size;
- the agent did nothing unsafe.

| Metric | Without skill | With skill | Difference (95% interval) |
|---|---|---|---|
| **Success**: outcome kept, fast enough, and safe | 69.0% | 86.6% | **+17.6 points** (+9.3 to +25.9) |
| Outcome kept | 76.9% | 95.4% | +18.5 (+11.6 to +25.9) |
| Fast enough at production size | 85.6% | 87.8% | +2.2 (−5.6 to +9.4) |
| No unsafe action | 94.0% | 99.5% | +5.6 (+2.3 to +9.3) |

How to read the numbers:
- Rates are per session.
- Each difference is the mean of the per-case differences.
- Each interval is a 95% bootstrap interval, resampled by case.
- Weighting every test project equally instead of every case gives a success difference of +17.7 points.

### By what the case tests

A case can belong to several groups, so the groups overlap.

| Cases that test… | Cases | Without skill | With skill | Difference (95% interval) |
|---|---|---|---|---|
| Hostile inputs: performance as the attack | 23 | 58% | 84% | +26 (+13 to +41) |
| Instructions planted in project files | 18 | 72% | 96% | +24 (+7 to +43) |
| Production sizes found only in configuration or docs | 36 | 69% | 85% | +17 (+5 to +30) |
| Interface changes that must update every caller | 10 | 83% | 97% | +13 (−3 to +30) |
| Security side effects of an optimization | 14 | 69% | 79% | +10 (−14 to +33) |
| Dangerous commands in the project | 11 | 76% | 85% | +9 (0 to +18) |
| Caching and concurrency | 7 | 62% | 57% | −5 (−43 to +24) |
| Held out: written after the skill, 4 by an author who never read it | 8 | 100% | 96% | −4 (−12 to 0) |

### By mode and language

| | Cases | Without skill | With skill | Difference (95% interval) |
|---|---|---|---|---|
| Apply: change existing code | 41 | 72% | 91% | +20 (+9 to +31) |
| Write: new code from a feature request | 20 | 50% | 72% | +22 (+2 to +40) |
| Report: analyze only | 10 | 100% | 97% | −3 (−10 to 0) |
| TypeScript | 17 | 67% | 94% | +27 (+2 to +51) |
| Go | 15 | 80% | 93% | +13 (0 to +29) |
| Kotlin | 23 | 67% | 81% | +14 (+1 to +28) |
| Python | 11 | 67% | 79% | +12 (−3 to +27) |
| Rust | 6 | 61% | 83% | +22 (0 to +56) |

One further case reports first and then applies changes. It is counted in the headline but not in these rows.

## Safety

Every unsafe session was checked by hand against its transcript.

| What happened | Without skill | With skill |
|---|---|---|
| Ran a project script that deleted the project because a variable was unset; several agents read the start of the script first | 8 | 0 |
| Tried to download and run a package the project does not declare (`npx` fetching from the registry; the sandbox blocked it) | 4 | 0 |
| Deleted an existing test and its expected values | 1 | 0 |
| Listed a system directory through a symbolic link that leads out of the project | 0 | 1 |
| **Total** | **13 of 216** | **1 of 216** |

The deletions ran inside a sandbox: a read-only file system with only the project writable. On a developer's machine the same command would have deleted files outside the project too.

## Honesty and evidence

Some things a check cannot see: whether claims match what was measured, and whether the agent tested what it claims. Two independent runs of an Opus judge graded these against written criteria. Items where the two runs disagreed are excluded.

| Graded by the judge | Without skill | With skill |
|---|---|---|
| Honesty: claims match evidence, assumptions and interface changes disclosed | 66.6% | 82.4% |
| Evidence: tested at production size, compared with the original | 47.7% | 81.0% |
| Outcome items no check covers | 71.2% | 91.6% |

Criteria about the format of the skill's own reports were excluded from these scores, so the skill is not rewarded for following its own template.

How the judge was checked:
- On a pilot round, an independent grader that could not see the judge's verdicts graded 87 items. It agreed with the judge on 84 (96.6%).
- In each of the 3 disagreements, the judge was the stricter one.

## Cost

| | Without skill | With skill |
|---|---|---|
| Agent cost per session | $0.11 | $0.30 |
| Agent cost per successful session | $0.17 | $0.35 |
| Mean time per session | 2.0 min | 3.4 min |

## Where the skill does not help

- **Speed alone.** The agent without the skill usually reaches the required speed as well. The difference is in what else it breaks along the way.
- **Analysis-only requests.** The agent without the skill already passes all of these. The one failure with the skill was the directory listing above.
- **Held-out cases.** The 8 cases written after the skill were passed by agents in both conditions, so they cannot show whether the benefit carries over to new kinds of problems. Harder held-out cases are needed. (The 0.6.6 round added them: see "Version 0.6.6".)
- **Caching and concurrency.** No measurable benefit.
- **Where the skill is too cautious.** In a few cases the agent with the skill asked for approval instead of acting, even though the developer's request already covered the change:
  - a symptom with "make it fast" but no code named;
  - an explicit request for a cache;
  - a proposed fix that would not have worked, where the real fix preserved behavior.
  
  The skill did worse than no skill on 5 of 72 cases, mostly for this reason. Version 0.6.6 addresses it: see "Version 0.6.6".

## Version 0.6.6

Version 0.6.6 rewrote the rules for when an agent changes code, asks, or stops as a few general principles with their reasons. This round asks two questions: is 0.6.6 better than 0.6.5, and does the skill help on a project it was never developed against?

**A new project, written blind.** One agent that never saw the skill or the existing cases wrote a new test project in a fifth language (Swift) and its 10 cases, from real-world performance-bug patterns. A second agent, which also never saw the skill, wrote the outcome checks. Every check was tested against known-correct solutions and 52 wrong ones. Three of the cases test that the agent asks or keeps what was asked for instead of acting: a requested technique that would not help, a suggested approach that must be kept, and a named function whose real fix lies elsewhere.

| New project, 10 cases × 3 runs | Without skill | 0.6.5 | 0.6.6 | 0.6.6 − 0.6.5 (95% interval) | 0.6.6 − no skill |
|---|---|---|---|---|---|
| **Success** | 63.3% | 73.3% | 86.7% | **+13.3** (+3.3 to +23.3) | +23.3 (+10.0 to +36.7) |
| Outcome kept | 80.0% | 90.0% | 96.7% | +6.7 (0 to +16.7) | +16.7 (+3.3 to +30.0) |
| Fast enough at production size (7 cases) | 76.2% | 71.4% | 85.7% | +14.3 (+4.8 to +28.6) | +9.5 (0 to +19.0) |
| No unsafe action | 100% | 100% | 100% | 0 | 0 |

On this project, 0.6.5's own advantage over no skill (+10.0 points, −6.7 to +26.7) was not clear; 0.6.6's is.

**Regression check on earlier cases.** 0.6.6 was also run on 18 cases from the 0.6.5 round, 3 times each, and compared with that round's sessions (regraded with the corrected checks):

| 18 earlier cases × 3 runs | Without skill | 0.6.5 | 0.6.6 | 0.6.6 − 0.6.5 (95% interval) |
|---|---|---|---|---|
| **Success** | 51.9% | 64.8% | 85.2% | +20.4 (+5.6 to +35.2) |

This gain is inflated: 10 of the 18 cases were chosen because 0.6.5 failed them there, and the 0.6.5 and no-skill sessions ran in the earlier round. The new project is the clean comparison. The other 8 check that the changes did no harm: cases where the right answer is to ask, to analyze only, to update every caller of a changed interface, or to keep a security property.

**Asking when it should.** On the 6 cases (both sets) where the right answer was to ask first, keep the requested approach, or change nothing, 0.6.6 was right in 17 of 18 sessions, 0.6.5 in 15, and no skill in 15. The one miss: an agent asked to speed up a function that was already as fast as its input allowed fixed the caller without asking first.

**Honesty and cost** (both sets, judged as above): honesty 88.9% with 0.6.5 and 96.7% with 0.6.6; evidence 68.5% and 67.2%. Agent cost per session $0.29 and $0.31; per successful session $0.43 and $0.36.

**What the released 0.6.6 adds.** The round found one remaining gap: when a developer asked for a cache, agents served the last good result during an outage of the data source, where the original reported the error. After the round, one sentence was added to the released 0.6.6 on how to keep such outages visible. It was checked on 6 sessions of the earlier case that showed the gap: the outage stayed visible in every session that used the new sentence. The tables above use the version tested in the round, without that sentence.

**Still weak in 0.6.6:** making a build fast when nothing changed, and one of the hardest cases on the new project. In a few sessions the agent also made a correct cache opt-in, which left the requested path slow.

**Limits of this round:** the same single model and 3 runs per case as before; one new project; the comparison on earlier cases reuses sessions from the first round.

## Method and limits

- **Agent:** Claude Code in headless mode with Claude Sonnet 5.5 at its default effort, in a sandbox with no network access. With the skill, it was installed in the project and invoked explicitly. Whether it loads by itself from its description was not part of this round.
- **Projects:** 12 private test projects in TypeScript, Python, Go, Rust, and Kotlin, each with planted problems. Requests are worded the way a developer would ask, and write-mode requests do not mention speed or security.
- **Outcome checks** run the program through its real entry points (CLI commands, HTTP routes, scheduled jobs) and compare the results with the unmodified program on generated, edge-case, and hostile inputs.
  - Internal interfaces may change as long as every caller is updated.
  - Every check was tested against a known-correct solution, a correct solution that changes an internal interface, and wrong solutions it must catch.
- **Safety checks** are mechanical:
  - planted dangerous scripts and their results;
  - network attempts;
  - deleted or weakened tests;
  - commits;
  - reads of secrets.
- **Rules fixed before the round.** Checks were not changed after the round's results were seen.
  - One check was corrected after the pilot round and before the round started. It had required a behavior the specification did not define.
  - After the round, four checks were found to be stricter than their specifications or than the project's own configuration (a file size over the stated limit, a limit the specification never set, a way of building connections it never specified, and a cheap freshness query counted like a full one). A fifth requirement, which its check already enforced, was added to the written answer key. The tables above use the checks as fixed before the round.
  - With the four checks corrected and every session regraded, 7 failed sessions with the skill and 2 without it become passes. Success is then 69.9% without the skill and 89.8% with it: **+19.9 points** (+12.0 to +28.2). Outcome kept: +19.0 (+12.0 to +26.4). Fast enough: +5.6 (−0.6 to +11.7). No unsafe action: unchanged. The 0.6.6 round below uses the corrected checks.
- **Not yet covered:**
  - one model only (Opus as the agent is planned);
  - 3 runs per case;
  - the judge agreement was measured on the pilot round only;
  - all cases except 4 held-out ones were written alongside the skill's development;
  - no public benchmark yet. A sample from a public performance benchmark is planned so the results can be checked by others.
