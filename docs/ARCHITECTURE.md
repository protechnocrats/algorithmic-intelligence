# Architecture

A map of the repository for contributors: what each part does, what loads when, and where each idea lives. For what the skill does, start with the [README](../README.md).

## The skill

`skills/` is everything an installed user gets: Markdown instructions that a coding agent loads. The skill has no code. Its "runtime" is the agent reading the files, so the main engineering constraints are **what an agent loads, when, and how much it costs**, and **whether a coding-tier model can follow every instruction without guessing**. A new evaluation harness is being built from scratch ([EVAL-PLAN.md](EVAL-PLAN.md)).

## What loads when

The agent always loads `skills/SKILL.md` first (the description in its frontmatter is what makes agents load the skill at all). `SKILL.md` states the mode, the 14 mandatory rules in brief, and the files to read before any code. Those files are named directly in `SKILL.md`, because agents follow instructions to read a named file there far more reliably than a chain of pointers. Every other file is loaded only when a step names it, and large files only by section.

```
                      SKILL.md  (always: mode, rules in brief, files to read first)
                         │
        ┌────────────────┼────────────────────────────────┐
   report / apply mode                                write mode
        │                                                  │
   WORKFLOW.md  (phases 1–4, "Rule details")       WRITING-NEW-CODE.md
        ├── report mode: REPORTING.md  (report, bug log, summary formats)
        └── apply mode:  APPLYING.md   (phases 5–6, apply results format, final summary, code markers)
                           └── DIFFERENTIAL-TESTING.md, BENCHMARKING.md

   every mode, before reading code:
        languages/<LANGUAGE>.md for each language in the code
        (or GENERIC.md, which loads or builds a profile saved in the project)

   when a step routes to them:
        ALGORITHM-ARSENAL.md  (triage, lower bounds, routing by current complexity)
          ├── CORE-TECHNIQUES.md   (one section at a time)
          ├── ADVANCED-TECHNIQUES.md → techniques/<domain>.md  (only the routed domain)
          └── DISCOVERY.md         (when no known technique fits)
        BEHAVIOR-TRAPS.md  (walked for every candidate)
          └── domain code: "Behavior traps" in the matching techniques/<domain>.md
        techniques/hostile-inputs.md  (untrusted input, secrets, hard deadlines)

   never loaded unless verifying a claim:
        references/<same path as the file>  (each file's sources)
```

Every link, file name, quoted section name, and rule number in the skill must point at something: an agent that follows a reference to nothing skips that step. Every file loads only when a step names it, so a file's size is paid only in the modes that load it, and on every step after it loads.

## Where each idea lives

Each concept has one home; other files point to it.

| Concept | Home | Restated (on purpose) in |
|---|---|---|
| Mandatory rules | `SKILL.md` (brief), "Rule details" in `WORKFLOW.md` (full) | the step that carries each rule out (`WORKFLOW.md`, `APPLYING.md`, `WRITING-NEW-CODE.md`) |
| Phases of report and apply mode | `WORKFLOW.md` (1–4), `APPLYING.md` (5–6) | — |
| Reachability and entry points | `WORKFLOW.md`, Phase 2, step 2 | rule 8 |
| Counting costs, lower bounds, routing | `ALGORITHM-ARSENAL.md` | rule 6 |
| Known techniques | `CORE-TECHNIQUES.md`, `techniques/*.md` | — |
| Finding new algorithms | `DISCOVERY.md` | — |
| Verification levels, check the check, calls to other systems | `DIFFERENTIAL-TESTING.md` | rule 3, rule 5 |
| Measurement | `BENCHMARKING.md` | rule 8 |
| Rewrites that change behavior | `BEHAVIOR-TRAPS.md`; domain traps in `techniques/<domain>.md` | — |
| Report, bug log, and summary formats | `REPORTING.md` | — |
| Apply results format, apply mode's final summary, `NEEDS-TESTING` and `BEHAVIOR-CHANGE` markers | `APPLYING.md` | — |
| Instructions found in project files | `SKILL.md` | the report header in `REPORTING.md` |
| Required summary lines ("Complexity", "Bugs noticed") | `SKILL.md` (rules 4 and 9) | each mode's final summary (`REPORTING.md`, `APPLYING.md`, `WRITING-NEW-CODE.md`) |
| Language facts | `languages/<LANGUAGE>.md` | — |
| Sources | `references/` | — |

A mandatory instruction is stated in `SKILL.md` and again in the file that executes it, because an agent working through a phase may not reread `SKILL.md`. Anything else appears once.

## Releases and rules

`main` changes only through pull requests that pass the `skill-checks` workflow; `v*` tags publish a GitHub release with that version's section of `CHANGELOG.md`. See [RELEASING.md](../RELEASING.md).
