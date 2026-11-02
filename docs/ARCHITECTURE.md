# Architecture

A map of the repository for contributors: what each part does, what loads when, and where each idea lives. For what the skill does, start with the [README](../README.md).

## Two halves

| Part | What it is | Who uses it |
|---|---|---|
| `skills/` | The skill: Markdown instructions that a coding agent loads. Everything an installed user gets. | Coding agents |
| `evals/` | The evidence: test projects with planted problems, answer keys, grading probes, and the scripts that run agent sessions and measure them. Never installed. | Maintainers and contributors |

The skill has no code. Its "runtime" is the agent reading the files, so the main engineering constraints are **what an agent loads, when, and how much it costs**, and **whether a small model can follow every instruction without guessing**.

## What loads when

The agent always loads `skills/SKILL.md` first (the description in its frontmatter is what makes agents load the skill at all). `SKILL.md` names the mode, holds the 14 mandatory rules, and routes to the other files. Every other file is loaded only when a step names it, and large files only by section.

```
                      SKILL.md  (always: modes, mandatory rules, routing)
                         │
        ┌────────────────┼──────────────────────────┐
   report / apply mode                          write mode
        │                                            │
   WORKFLOW.md  (phases 1–6)                 WRITING-NEW-CODE.md
        │                                            │
        ├── languages/INDEX.md → one companion file per language
        │      (or GENERIC.md, which builds and saves a profile in the project)
        ├── ALGORITHM-ARSENAL.md  (triage, lower bounds, routing by current complexity)
        │      ├── CORE-TECHNIQUES.md   (one section at a time)
        │      ├── ADVANCED-TECHNIQUES.md → techniques/<domain>.md  (only the routed domain)
        │      └── DISCOVERY.md         (when no known technique fits)
        ├── REPORTING.md          (report and apply-results formats)
        └── apply mode adds: DIFFERENTIAL-TESTING.md, BEHAVIOR-TRAPS.md, BENCHMARKING.md
```

`evals/check-refs.py` checks that every link, file name, quoted section name, and rule number in the skill still points at something, so a rename cannot leave an agent following a reference to nothing.

`evals/token-budget.sh` measures exactly this loading per mode and fails when it grows past a budget. Budgets make growth visible; when a needed instruction exceeds one, the budget is raised (with the reason recorded in the script), never met by trimming instructions.

## Where each idea lives

Each concept has one home; other files point to it.

| Concept | Home | Restated (on purpose) in |
|---|---|---|
| Mandatory rules | `SKILL.md` | the phase that carries each rule out (`WORKFLOW.md`, `WRITING-NEW-CODE.md`) |
| Phases of report and apply mode | `WORKFLOW.md` | summary in `SKILL.md` |
| Counting costs, lower bounds, routing | `ALGORITHM-ARSENAL.md` | rule 6 |
| Known techniques | `CORE-TECHNIQUES.md`, `techniques/*.md` | — |
| Finding new algorithms | `DISCOVERY.md` | — |
| Verification levels, check the check, calls to other systems | `DIFFERENTIAL-TESTING.md` | rule 3, rule 5 |
| Measurement | `BENCHMARKING.md` | rule 8 |
| Rewrites that change behavior | `BEHAVIOR-TRAPS.md` | — |
| Report formats | `REPORTING.md` | — |
| Language facts | `languages/<LANGUAGE>.md` | — |

A mandatory instruction is stated in `SKILL.md` and again in the file that executes it, because an agent working through a phase may not reread `SKILL.md`. Anything else appears once.

## The evaluation pipeline

```
fixtures/<project>   ──new-run.sh──▶  a fresh git repo outside this one (+ the skill, for with-skill runs)
                                             │
                             run-pilot.sh: claude -p, three turns (report, "apply all", decline)
                                             │  logs/<session>.*.jsonl, progress.log
                    ┌────────────────────────┼─────────────────────────┐
             probes/<project>         answers/<project>.md        cost-breakdown.py, session-stats.py
         (trap inputs, original     (expected outcome per case,    (cost by activity, refusals,
          vs the session's code)     why a baseline fails)          skill files read)
                    └────────────────────────┴──────────────▶ results/<date>-<round>.md
```

- **Fixtures** are small projects with planted cases. **Tuning** fixtures may shape the skill's wording; **held-out** ones (`py-logistics`, `rb-clinic`) only measure it.
- **Probes** compare a session's final code with the original fixture on trap inputs. `evals/probes/selftest/` holds a correct and a deliberately wrong rewrite for each probed case, and `evals/selftest.sh --probes` checks that the probe accepts the first and catches the second.
- **Report grader:** `evals/check-report.py` checks a session's report files for every field the templates in `REPORTING.md` require. It reads the fields from the templates, so it follows format changes.
- **Rule evidence:** `evals/rule-cases.py` builds [RULE-EVIDENCE.md](RULE-EVIDENCE.md) from the answer keys: which cases test each rule.
- **The runner** caps spending (`--max-total-usd`), stops stalled turns, and never lets a stopped session end the batch. `evals/selftest.sh` tests it with a stub agent at no cost.

## Releases and rules

`main` changes only through pull requests that pass the `skill-checks` workflow; `v*` tags publish a GitHub release with that version's section of `CHANGELOG.md`. See [RELEASING.md](../RELEASING.md).
