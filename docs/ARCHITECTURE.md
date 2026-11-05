# Architecture

A map of the repository for contributors: what each part does, what loads when, and where each idea lives. For what the skill does, start with the [README](../README.md).

## The skill

`skills/` is everything an installed user gets: Markdown instructions that a coding agent loads. The skill has no code. Its "runtime" is the agent reading the files, so the main engineering constraints are **what an agent loads, when, and how much it costs**, and **whether a coding-tier model can follow every instruction without guessing**. A new evaluation harness is being built from scratch ([EVAL-PLAN.md](EVAL-PLAN.md)).

`plugin/` is separate and optional: guard hooks for Claude Code (and Grok Build, which reads Claude Code plugins) that back the rules prose cannot guarantee. `scripts/guard.py` is a PreToolUse hook that asks the developer before commits, git commands that discard uncommitted work, root, risky permission or ownership changes, piped installs, installs outside the project, deletes outside the project or of a `.git` directory, secret-file reads, and edits to existing tests; `scripts/summary_check.py` is a Stop hook that checks the final-summary lines when the skill was used. Both fail open, and `tests/` covers them (`python3 -m unittest discover -s plugin/tests`, also run by the `skill-checks` workflow). `.claude-plugin/marketplace.json` at the repository root lists the plugin for installation. A rule belongs in a hook only when it must hold every time and can be checked mechanically; everything that needs judgment stays in the skill.

## What loads when

The agent always loads `skills/SKILL.md` first. The description in its frontmatter is what makes agents load the skill at all: it says what the skill does and when to use it, in terms of the intent and the kind of work (something slow, costly, or scaling badly, however the symptom is put; code that processes, looks up, or moves data being written or changed), with one exclusion, and does not summarize the workflow or list trigger phrases, so any wording of that intent matches. `SKILL.md` is kept under about 5,000 tokens, with the safety sections first, because some agents keep only the start of a skill after compacting a long conversation. It holds each cross-cutting rule once, with its reason, and a table naming every other file with the moment to open it, so every file is one step from `SKILL.md`. The mode files hold the full form of the rules and the output formats; the technique and language files are reference material read when a step needs them.

The skill is written for a capable model: goals, the reasons behind them, the heuristics that decide hard cases, and the facts a model may not know (hidden costs, preconditions, traps). It avoids step-by-step procedure the agent would follow anyway and lists of cases a stated principle already covers. When an evaluation finds a failure, the fix is the missing principle, routing, or fact, not the words of the case that failed.

```
                      SKILL.md  (always: mode, rules in brief, files to read first)
                         │
        ┌────────────────┼────────────────────────────────┐
   report / apply mode                                write mode
        │                                                  │
   WORKFLOW.md  (phases 1–4, "Rule details")       WRITING-NEW-CODE.md
        ├── report mode: REPORTING.md  (report, bug log, summary formats)
        └── apply mode:  APPLYING.md   (phases 5–6, apply results format, final summary, code markers)
                           └── BENCHMARKING.md

   every mode, before reading code:
        languages/<LANGUAGE>.md for each language in the code
        (or GENERIC.md, which loads or builds a profile saved in the project)

   every mode, before writing any differential test (apply mode's tests, and
   write mode's tests against a reference version):
        DIFFERENTIAL-TESTING.md

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
| Translating the request (goal, symptom to code, sizes from facts, business constraints, problem underneath) | `SKILL.md` | "Request as understood" in each mode's output (`REPORTING.md`, `APPLYING.md`, `WRITING-NEW-CODE.md`) |
| Untrusted content (project text and earlier sessions' files are evidence, not instruction; approval only from the developer in the conversation) | "Untrusted content" in `SKILL.md` | the report header in `REPORTING.md`; the saved-profile checks in `languages/GENERIC.md` |
| Reading commands before running them, and what never runs | "Before running a command" in `SKILL.md` | the test-suite step in `WORKFLOW.md`, Phase 1; the "Commands not run" line of each final summary |
| Risky requests, runs where nobody can approve | "When the request itself is risky" in `SKILL.md` | — |
| Speedups that weaken a security property | "Security-sensitive behavior" in `BEHAVIOR-TRAPS.md` | "When the request itself is risky" in `SKILL.md`; "Security is behavior" under rule 5 in `WORKFLOW.md` |
| Required summary lines ("Complexity", "Bugs noticed", "Commands not run", "Hazards noticed", and "Waiting for approval" in runs where nobody can answer) | "Every final summary" in `SKILL.md` | each mode's final summary (`REPORTING.md`, `APPLYING.md`, `WRITING-NEW-CODE.md`); the Stop hook in `plugin/` checks the first four |
| Language facts | `languages/<LANGUAGE>.md` | — |
| Sources | `references/` | — |

A mandatory instruction is stated in `SKILL.md` and again in the file that executes it, because an agent working through a phase may not reread `SKILL.md`. Anything else appears once.

Every file in `skills/` is an instruction that every user's agent follows, so a change to it is reviewed like code: wording that widens what the agent may run, approve, or skip is a security change (see [SECURITY.md](../SECURITY.md)). Files the skill writes into a user's project (reports, bug logs, saved language profiles) are read back by later sessions as untrusted data, never as instructions.

## Releases and rules

`main` changes only through pull requests that pass the `skill-checks` workflow; a version tag (`0.3.0`; `v*` before 0.3.0) publishes a GitHub release with that version's section of `CHANGELOG.md`. See [RELEASING.md](../RELEASING.md).
