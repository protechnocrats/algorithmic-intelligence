# Evaluation plan: adversarial inputs, security, unusual problems, and write mode on Sonnet and Opus

Status: proposed. Nothing in this plan spends money until its phase's cap is agreed. The harness, fixtures, and results are built from scratch: no earlier ones carry over. Fixtures, answer keys, and the individual cases stay out of this repository, so cases remain held out; aggregate results of full rounds are published in [RESULTS.md](RESULTS.md) without anything that identifies a case. This file holds the method and the categories tested. The cases themselves (traps, probe inputs, fixtures, sample sizes, and budgets) are in a private file under `evals/`, which is not tracked.

## Why

- **Write mode needs its own evaluation.** It is the mode most developers will hit (new code, loaded from the skill's description), and it needs its own cases and grading. Every round runs report **and** write mode.
- **Headline metrics come from coding-tier models** (Sonnet and Opus), the models the skill is written for.
- **Probes alone undercount strong-model failures.** A probe tests only the inputs it was written for. A judge model reading each session's code and reports can catch behavior changes no probe checked, such as those in group C below. Grade with both.
- **Cases must not be textbook.** Strong models solve textbook problems without the skill. Its value for them is in what they miss: hostile inputs, security side effects of an optimization, problems with no textbook answer, and keeping contracts under pressure.

## What we test: the categories

Every case gets an answer key (Pass / Fail lines, rules tested), a probe check that runs on the session's final code, and a correct and a wrong self-test rewrite that the probe must pass and catch. The skill is a performance skill, not a security scanner: the security cases test **whether an optimization opens a hole, or a performance problem is itself the attack**, and whether existing security bugs are reported (rule 4) rather than silently fixed or widened.

- **A. Hostile inputs: performance as the attack** (CWE-407 and relatives). Inputs chosen to reach a structure's or algorithm's worst case, inputs whose size or depth the user controls, and inputs that expand in memory. Pass means a worst-case-safe structure or a bound, with exposure stated, and the same accepted inputs as before. Patterns come from CWE-407's examples and published advisories, reimplemented in our own code; vulnerable code is never copied from the projects in those advisories (licenses, and the models have seen the fixes).
- **B. Security: optimizations that open a hole.** Batching, caching, work removal, and arithmetic changes that would introduce injection, cross-user leaks, removed checks, timing differences, time-of-check-to-time-of-use gaps, or overflow, and existing security bugs in code the agent optimizes. Pass means the protection is kept, the leak or bug is named in the report, and nothing is fixed on purpose or made worse (rules 4 and 5).
- **C. Contracts strong models break.** Edge values, size limits the optimization introduces, numeric identity, returned values that callers mutate, error type and order, and batch calls without a fallback.
- **D. Problems with no textbook answer.** A textbook problem with one constraint that breaks the standard algorithm; code whose intuition is wrong (looks quadratic but is amortized linear); provably tiny inputs on a cold path; bottlenecks outside the CPU; numerical rewrites; and problems taken from outside sources and changed so they are not memorized.
- **E. Untrusted content and unsafe commands.** The skill's own safety rules ("Untrusted content", "Before running a command", "When the request itself is risky" in `SKILL.md`), tested in every mode: text addressed to AI assistants in project files and program output, forged approvals and markers, commands and tests that delete, escalate, or reach a fake "production" host, side effects under differential tests, tampered files from earlier sessions, requests to skip a safety rule, and headless runs. Every "production" host, credential, and mail server in these cases is a local fake that records what reaches it; the probe checks it received nothing.

### Outside sources

- **Real-world optimization benchmarks** as a separate track, for numbers others can check: [GSO](https://arxiv.org/abs/2505.23671) (102 tasks from 10 codebases), [SWE-Perf](https://arxiv.org/abs/2507.12415) (140 instances from real performance pull requests), and SWE-fficiency (498 tasks). Before use, check each one's license, harness, and cost per task, and whether it runs with Claude Code. A sample of 10 to 20 tasks, skill against baseline, on Sonnet.
- **Competitive programming and puzzle problems** only as seeds for group D, never as is: public problems and their solutions are in the models' training data. Change the constraints so the known solution no longer applies.
- **Security advisories** as patterns for A and B, reimplemented.

## Write mode

Each fixture gets write cases phrased the way a developer would ask, with no mention of speed or security, so the skill has to notice the hidden scale, the hidden N+1, the hidden injection, the hidden hostile input, or the hidden cross-user state in an ordinary feature request.

Every write case runs in two loading conditions: description only (the skill must trigger by itself) and with the README's `CLAUDE.md` line.

The grader's write-mode section checks:
- loaded, by description or by the instruction line;
- mode stated;
- correct on the reference cases;
- time at the stated volume and on hostile inputs;
- security probes passed;
- performance decisions listed;
- existing code changed only as far as the request needs;
- cost.

## How we test

- **Models:** Sonnet 5.5 is the primary model. Opus 5.5 confirms the result. Haiku appears only as a cheap smoke test of the harness, never in metrics.
- **Conditions:** with the skill against without, the same fixture, model, and prompts. Write mode also compares description-only loading with the instruction line.
- **Held out:** a fixture's answer key is not used to change the skill until its round is graded. After that it is a development fixture, and the results say so.
- **Environment:** the dev container, with Claude Code's permission prompts skipped (`--dangerously-skip-permissions`, safe only inside the container), so permission refusals do not invalidate sessions. The container holds no real credentials, and its network reaches only the local fakes, because sessions run fixture code that is designed to be hostile. A skipped-permissions session is a non-interactive run: the skill must leave approval items pending, and the grader counts that as correct.
- **Grading:** every category in the grader's rubric, including the write-mode and security rows, in every round. The judge's rubric gets the security checks.
  - **Judge model:** Sonnet sessions are judged by Opus, so no model grades its own output. Keep the judge fixed across rounds that are compared.
  - **Judge check:** before each round, run the judge on sessions with known correct grades and confirm it reproduces them.
- **Sample size:** several pairs per fixture and mode on each model, recorded as counts, never a percentage alone, in the private results. The numbers are in the private case file.

## Phases and gates

Costs are estimated per phase and re-estimated after the pilot measures cost per session; the caps and fixture details are in the private case file.

1. **Harness:** a runner that drives Claude Code headless with a spending cap; a grader with its rubric, including write-mode and security rows; probes for groups A to E, with a self-test that runs each probe on its correct and wrong rewrites; Opus as judge. Gate: self-tests pass.
2. **Cases:** held-out fixtures with probes, self-test rewrites, and answer keys. Gate: every probe check passes its correct rewrite and catches its wrong one.
3. **Pilot:** one pair per fixture, report and write. Gate: measured cost per session; the cases are neither trivial nor impossible for Sonnet; a cap for the main round agreed.
4. **Main round:** both models, both modes, every fixture. Gate: full scorecard.
5. **Outside benchmark:** a sample of tasks from GSO or SWE-Perf, skill against baseline, after the license and harness check.
6. **Fix and confirm:** skill changes for the failures found, then an A/B round (old skill against new) on the same cases. Gate: the new skill is no worse on any category, and better where it was aimed.

## What this plan does not cover

- **Other agents** (Codex CLI, Gemini CLI). The runner drives Claude Code only. Supporting another agent is separate work, needed before the skill can claim "any agent" from evidence.
- **A security review of real projects.** The security cases test the skill's own failure modes, not general vulnerability finding.
