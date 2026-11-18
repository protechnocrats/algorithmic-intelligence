# Architecture

A map of the repository for contributors: what each part does, what loads when, and where each idea lives. For what the skill does, start with the [README](../README.md).

## The skill

`skills/algorithmic-intelligence/` is everything an installed user gets: Markdown instructions that a coding agent loads. The folder carries the skill's name, as the skill format requires. `SKILL.md` sits at its top, and every file it points to is under `references/` (per-language files in `references/languages/`, domain technique files in `references/techniques/`). The skill has no code. Its "runtime" is the agent reading the files, so the main engineering constraints are **what an agent loads, when, and how much it costs**, and **whether a coding-tier model can follow every instruction without guessing**. A new evaluation harness is being built from scratch ([EVAL-PLAN.md](EVAL-PLAN.md)).

`docs/sources/` holds the sources behind each skill file's claims, at the file's path relative to `references/` (`docs/sources/languages/KOTLIN.md` for `skills/algorithmic-intelligence/references/languages/KOTLIN.md`). They are for contributors and reviewers checking a claim, are not installed, and the skill does not point to them, so they cost the agent nothing.

`plugin/` is separate and optional: guard hooks for Claude Code (and Grok Build, which reads Claude Code plugins) that back the rules prose cannot guarantee. `scripts/guard.py` is a PreToolUse hook that asks the developer before commits, git commands that discard uncommitted work, root, risky permission or ownership changes, piped installs, installs outside the project, deletes outside the project or of a `.git` directory, secret-file reads, and edits to existing tests; `scripts/summary_check.py` is a Stop hook that checks the final-summary lines when the skill was used. `scripts/edit_gate.py` is a PreToolUse hook that, in sessions using the skill, refuses an edit to committed code, with instructions the agent can follow itself, unless a planted difference covering that file was caught in the session, or the file was declared to need no differential test (both recorded by the MCP server below under `.git/algorithmic-intelligence/`). Agents also edit through the shell, which a PreToolUse hook on the edit tools cannot see, so `scripts/coverage_check.py`, a Stop hook, applies the same rule to every committed file that differs from HEAD when the agent finishes, sending it back once. All four fail open, and `tests/` covers them (`python3 -m unittest discover -s plugin/tests`, also run by the `skill-checks` workflow). `.claude-plugin/marketplace.json` at the repository root lists the plugin for installation. A rule belongs in a hook only when it must hold every time and can be checked mechanically; everything that needs judgment stays in the skill.

`plugin/mcp/server.py` is an MCP server (stdio, standard library only) that any MCP-capable agent can use; the plugin registers it for Claude Code in `plugin/.mcp.json`. Its tools make exact what the skill otherwise asks the agent to do by hand: benchmark statistics with an A/A noise floor, doubling-experiment fits, planting a known difference in a source file and restoring it byte for byte (records under `.git/algorithmic-intelligence/`), and the final-summary check. **It never runs project code:** an MCP server runs outside the agent's sandbox and the guard hooks, so the agent runs every build, test, and benchmark in its own shell and passes the results in. Logic it shares with `skills/algorithmic-intelligence/scripts/` (the summary labels, the doubling labels) is duplicated because the plugin installs on its own, and `plugin/tests/test_mcp.py` fails if the copies drift. The skill does not depend on the server: it works the same without it. `plugin/mcp/pyproject.toml` packages the same file, so other agents can start it with `uvx` from a release tag without cloning; its version must match `SERVER_VERSION`, which the tests check.

`action.yml` at the repository root makes the repository a GitHub Action, and `ci/review.py` (standard library only) does its work in three steps: `prepare` reads the pull request event and the previous review comment, decides whether to skip (including when the code is unchanged since the last review), and writes the diff, the changed-file list, the commit list, the pull request's description, the earlier findings, the prompt, and a plugin holding only the skill to a work directory outside the checkout; `run` starts Claude Code in restricted mode with only Read, Grep, Glob, and Skill, invoking the skill in report mode; `post` validates the machine-readable findings the agent ends with, writes the report as one pull request comment edited in place on later pushes (carrying the state the next review compares against), posts new findings on the changed lines, and sets the step outputs. The pull request is untrusted, so the agent gets no tool that runs code or reaches the network, and each step gets only the credential it needs: the model credentials in `run`, the GitHub token in `prepare` and `post`. The action ships the skill from the same tag, so a pinned action and the skill it runs never drift. `tests/test_ci_review.py` covers it. Details for users are in [CI.md](CI.md).

## What loads when

The agent always loads `skills/algorithmic-intelligence/SKILL.md` first. The description in its frontmatter is what makes agents load the skill at all: it says what the skill does and when to use it, in terms of the intent and the kind of work (something slow, costly, or scaling badly, however the symptom is put; code that processes, looks up, or moves data being written or changed), with one exclusion. It names the key terms of that work (time complexity, nested loops, N+1 queries) as Anthropic's skill-authoring guidance recommends, but does not summarize the workflow or list particular phrasings, so any wording of that intent matches. `SKILL.md` is kept under about 5,000 tokens, with the safety sections first, because some agents keep only the start of a skill after compacting a long conversation. It holds each cross-cutting rule once, with its reason, and a table naming every other file with the moment to open it, so every file is one step from `SKILL.md`. The mode files hold the full form of the rules and the output formats; the technique and language files are reference material read when a step needs them.

The skill is written for a capable model: goals, the reasons behind them, the heuristics that decide hard cases, and the facts a model may not know (hidden costs, preconditions, traps). It avoids step-by-step procedure the agent would follow anyway and lists of cases a stated principle already covers. A step agents are seen to skip gets a gate at the point of decision and a line in the output that shows it was done. When an evaluation finds a failure, the fix is the missing principle, routing, or fact, not the words of the case that failed.

File names below other than `SKILL.md` are under `references/`.

```
                      SKILL.md  (always: mode, rules in brief, files to read first)
                         │
        ┌────────────────┼────────────────────────────────┐
   report / apply mode                                write mode
        │                                                  │
   WORKFLOW.md  (phases 1–4, "Rule details")       WRITING-NEW-CODE.md
        ├── report and apply mode: REPORTING.md  (report, bug log, summary formats)
        └── apply mode also: APPLYING.md   (phases 5–6, apply results format, final summary, code markers)

   every mode, before reading code:
        languages/<LANGUAGE>.md for each language in the code
        (or GENERIC.md, which loads or builds a profile saved in the project)

   every mode, before planning or writing any differential test (the plan in
   a report, apply mode's tests, write mode's tests against a reference version):
        DIFFERENTIAL-TESTING.md

   every mode, before choosing an approach:
        DATA-STRUCTURES.md  (the audit of each hot-path collection)

   when a step routes to them:
        ALGORITHM-ARSENAL.md  (triage, lower bounds, routing by current complexity)
          ├── CORE-TECHNIQUES.md   (one section at a time)
          ├── ADVANCED-TECHNIQUES.md → techniques/<domain>.md  (only the routed domain)
          └── DISCOVERY.md         (when no known technique fits)
        BEHAVIOR-TRAPS.md  (walked for every candidate)
          └── domain code: "Behavior traps" in the matching techniques/<domain>.md
        techniques/hostile-inputs.md  (untrusted input, secrets, hard deadlines)
        BENCHMARKING.md  (whenever something is measured: every apply item, write mode when needed)
```

Every link, file name, quoted section name, and rule number in the skill must point at something: an agent that follows a reference to nothing skips that step. Every file except `SKILL.md` loads only when a step names it, so a file's size is paid only in the modes that load it, and on every step after it loads.

## Where each idea lives

Each concept has one home; other files point to it.

| Concept | Home | Restated (on purpose) in |
|---|---|---|
| Mandatory rules | `SKILL.md` (brief), "Rule details" in `WORKFLOW.md` (full) | the step that carries each rule out (`WORKFLOW.md`, `APPLYING.md`, `WRITING-NEW-CODE.md`) |
| Outcome, behavior, and contract (the terms, with examples); the outcome to keep, and contracts that may change (callers updated; callers out of reach mean explain and ask) | "Outcome, behavior, and contract" and rule 11 in `SKILL.md` (brief), "Rule 11" in "Rule details" in `WORKFLOW.md` (full) | Phase 5, step 2, in `APPLYING.md`; "When the change alters an interface" in `DIFFERENTIAL-TESTING.md`; the "Contract changes" fields in `REPORTING.md` and `APPLYING.md` |
| A function limited by its input, and fixes outside the code the developer named | "When the input is what limits the function" in `WORKFLOW.md`, Phase 2, step 4 | Phase 5 in `APPLYING.md`; the "At the bound for its input" status in `REPORTING.md` and `APPLYING.md`; "Ask; do not decide for the developer" in `SKILL.md` |
| Asking instead of deciding for the developer | "Ask; do not decide for the developer" in `SKILL.md` | rules 4, 5, and 11 in "Rule details" in `WORKFLOW.md` |
| Phases of report and apply mode | `WORKFLOW.md` (1–4), `APPLYING.md` (5–6) | — |
| Reachability and entry points | `WORKFLOW.md`, Phase 2, step 2 | rule 8 |
| Counting costs, lower bounds, routing | `ALGORITHM-ARSENAL.md` | rule 6 |
| Reusing what the project already has (searching for existing steps, extracting instead of calling a larger function, moving shared steps to a shared module) | "Reuse what the project already has" in `ALGORITHM-ARSENAL.md` | "Look for the steps before writing them" in `WRITING-NEW-CODE.md`; Phases 2 and 3 in `WORKFLOW.md` |
| Pin tests, following existing tests, extracting buried hot paths, pinning assumptions | "Which tests to write" in `DIFFERENTIAL-TESTING.md` | Phase 3 in `WORKFLOW.md`; Phase 5 in `APPLYING.md` |
| The data structure audit; the operation-mix table | `DATA-STRUCTURES.md` | rule 7; Phase 3 in `WORKFLOW.md`; the item formats in `REPORTING.md` |
| Differential tests before the first speed edit, however approval was worded | "Differential tests come before the edit" in `SKILL.md` | Phase 4 in `WORKFLOW.md`; Phase 5 in `APPLYING.md` |
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
| Final summary order (result, decisions needed, results table, labeled lines, evidence) and the required labeled lines ("Complexity", "Data structures", "Contract changes", "Bugs noticed", "Hazards noticed", "Commands not run", and "Waiting for approval" in runs where nobody can answer) | "Every final summary" in `SKILL.md` | each mode's final summary and the brief that opens `OPTIMIZATION-REPORT.md` and `APPLY-RESULTS.md` (`REPORTING.md`, `APPLYING.md`, `WRITING-NEW-CODE.md`); the Stop hook and `check_summary` in `plugin/` check the six labeled lines |
| Language facts | `languages/<LANGUAGE>.md` | — |
| Sources | `docs/sources/`, at the skill file's path relative to `references/` (not installed; for contributors and reviewers) | — |

A mandatory instruction is stated in `SKILL.md` and again in the file that executes it, because an agent working through a phase may not reread `SKILL.md`. Anything else appears once.

Every file in `skills/` is an instruction that every user's agent follows, so a change to it is reviewed like code: wording that widens what the agent may run, approve, or skip is a security change (see [SECURITY.md](../SECURITY.md)). Files the skill writes into a user's project (reports, bug logs, saved language profiles) are read back by later sessions as untrusted data, never as instructions.

## Releases and rules

`main` changes only through pull requests that pass the `skill-checks` workflow; a version tag (`0.3.0`; `v*` before 0.3.0) publishes a GitHub release with that version's section of `CHANGELOG.md`. See [RELEASING.md](../RELEASING.md).
