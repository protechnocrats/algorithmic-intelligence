# Evaluation results

Does loading the skill make a coding agent's result better, and never worse or less safe? And what does it cost? The table compares the same agent with and without the current release (0.7.0, with its optional plugin) on 46 cases from 13 private projects in six languages, each run 3 times per condition. The method is in [EVAL-PLAN.md](EVAL-PLAN.md). The cases, projects, and answer keys are private, so the skill cannot be tuned to them; this page reports aggregates only.

| 46 cases × 3 runs | No skill | 0.7.0 | Difference (95% interval) |
|---|---|---|---|
| **Success**: outcome kept, fast enough, and safe | 69.3% | 94.9% | **+25.0** (+14.5 to +37.0) |
| Outcome kept | 78.1% | 97.8% | +19.2 (+9.4 to +30.1) |
| Fast enough at production size (39 cases) | 82.8% | 95.7% | +12.8 (+5.1 to +22.2) |
| No unsafe action | 98.5% | 100% | +1.4 (0 to +3.6) |
| Honesty: claims match the evidence (judged) | 79.3% | 86.5% | |
| Evidence: tested at production size, compared with the original (judged) | 32.9% | 73.8% | |
| Success on caching cases (10) | 90.0% | 100% | +10.0 (0 to +30.0) |
| Success on concurrency cases (12) | 83.3% | 100% | +16.7 (0 to +36.1) |
| Success on held-out cases (42)¹ | 68.8% | 94.4% | +25.0 (+14.3 to +36.5) |
| Agent cost per session | $0.13 | $0.38 | |
| Agent cost per successful session | $0.19 | $0.40 | |
| Mean time per session | 1.9 min | 3.7 min | |

1. Written after the skill, most by agents that never saw it, including a Swift project, a GPU project on a modeled device, and a caching and concurrency project.

**How to read it.** A session succeeds only if the program's outcome is unchanged (checked through its real entry points against the unmodified program on generated, edge-case, and hostile inputs), it is fast enough at production size, and the agent did nothing unsafe (mechanical checks for planted dangerous scripts, network use, weakened tests, commits, and secret reads). Rates are per session; each difference is the mean of the per-case differences, with a 95% bootstrap interval resampled by case. Honesty and evidence are graded against written criteria by two independent runs of a judge model, with disagreements excluded; criteria about the skill's own report format are left out, so the skill is not rewarded for following its template.

**Limits.**
- One agent and model: Claude Code with Claude Sonnet 5.5, at default effort, sandboxed with no network. 3 runs per case, except 3 of the 276 sessions that the budget cut off.
- Most of the older cases were kept because earlier versions failed them, which favors the skill.
- 28 cases ran the 0.7.0 release candidate, which lacks the final changes to reporting and security approvals; on the 8 cases those changes target, the released files matched or beat the candidate on every measure.
- Making a build fast when nothing changed is still unsolved in both conditions.
- One case was dropped after the run: its answer key failed agents for making a configuration change the developer explicitly asked for, while warning about the problem it left. Both conditions failed it identically. A second check was narrowed so that documenting a change in the README no longer counts as tampering; this changed one session with the skill.
