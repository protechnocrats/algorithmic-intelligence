# Results overview

Each round has its own file with the method, every number, and its limits. This page summarizes them; the round files are the source.

| Round | File | Model | What it measured | Headline |
|---|---|---|---|---|
| Pilot, 2 | `2026-10-29-pilot.md`, `2026-10-29-round2.md` | Opus 5.5 | ts-shop, skill against no skill | Baselines failed T3, T5, T8, T10, T12 (prototype keys, deliberate bug fixes, stale indexes, stack overflow); the skill passed them |
| 3 | `2026-10-31-round3.md` | Opus 5.5, Haiku 5.5 | held-out py-logistics; skill versions; a second model | Report flow: 1.00 with the skill against 0.50 without (Opus), 0.83 against 0.39 (Haiku). Every baseline applied an unapproved concurrency change and shipped a quadratic-under-attack fix |
| Triggers | `2026-10-29-trigger.md`, `2026-10-31-trigger.md` | Opus 5.5, Haiku 5.5 | which prompts load the skill | Haiku rarely loads skills from the description; the README's project-instruction line fixes most of it (22 of 24) |
| 4 (partial) | `2026-11-01-round4-partial.md` | Haiku 5.5 | java-clinic, skill only | No behavior difference in 3 sessions; found that report close-out could overwrite the analysis, and permission refusals in the harness |
| 5 | `2026-11-01-round5-cost.md` | Haiku 5.5 | cost levers, before and after | Batching tool calls: quality kept, twice as fast, same cost. Medium effort: a third cheaper, same code, thinner reports. Noise about $0.20 per session |
| 6 | `2026-11-01-round6-report.md` | Haiku 5.5 | two-file report format | Report about 40% smaller, never rewritten; one valid session |
| 7 | `2026-11-01-round7.md` | Haiku 5.5 | held-out rb-clinic; java-clinic baseline; write mode | rb-clinic: no behavior change with the skill, the baseline corrupted labels. java-clinic: the baseline's change was 3.5 times slower under attack, which none of 11 skill sessions did. Write mode loaded the skill with the project-instruction line |
| 8 | `2026-11-02-round8.md` | Haiku 5.5, Opus 5.5 | held-out rb-clinic, 5 Haiku and 3 Opus pairs | Haiku: behavior differences in 0 of 5 with the skill, 4 of 5 without (label corruption). Opus: 0 of 3 in both, and the baseline was faster and cheaper. Haiku with the skill held back two speedups as behavior changes where equivalent variants existed |

## Case history: java-clinic and rb-clinic

Probe results per case: **=** same behavior as the original, **✗** a behavior difference, **slow** correct but slower under attack, **–** not run.

| Case | Skill (rounds 4 to 8) | Baseline (rounds 7 and 8) |
|---|---|---|
| J1 to J8, J10 | = in every session | = |
| J9 (hostile input) | = and fast in 10, unchanged in 1 | **slow**: 12.0 s against 3.4 s for the original |
| JW1 (write mode) | = (1 session) | = (1 session) |
| RB1 | = in 10; cut to 40 round trips in 1 | = in 9; cut to 40 in 8 |
| RB3 to RB9 | = (10 sessions) | = (9 sessions) |
| RB2 (aliasing) | = in 10; fixed safely in 4 (1 Haiku, 3 Opus) | **✗** in 5 of 6 Haiku (labels corrupted); = and fixed in 3 of 3 Opus |
| RBW1 (write mode) | = (1 session) | = (1 session) |

## What is still missing

- More than one java-clinic baseline, and Opus on java-clinic.
- Any agent other than Claude Code.
- kotlin-shop, swift-shop, c-shop, and rust-shop have answer keys but no runs; Swift has not been compiled.
