# Architecture

A map of the repository for contributors: what each part does, what loads when, and where each idea lives. For what the skill does, start with the [README](../README.md).

## The skill

`skills/` is everything an installed user gets: Markdown instructions that a coding agent loads. The skill has no code. Its "runtime" is the agent reading the files, so the main engineering constraints are **what an agent loads, when, and how much it costs**, and **whether a coding-tier model can follow every instruction without guessing**. A new evaluation harness is being built from scratch ([EVAL-PLAN.md](EVAL-PLAN.md)).

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

Every link, file name, quoted section name, and rule number in the skill must point at something: an agent that follows a reference to nothing skips that step. Every file loads only when a step names it, so a file's size is paid only in the modes that load it.

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

## Releases and rules

`main` changes only through pull requests that pass the `skill-checks` workflow; `v*` tags publish a GitHub release with that version's section of `CHANGELOG.md`. See [RELEASING.md](../RELEASING.md).
