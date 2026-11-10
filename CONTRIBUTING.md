# Contributing

Thank you for helping. This project is a skill: Markdown instructions that coding agents follow. Read [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) first. It shows which file holds what, and what an agent loads when.

## What helps most

- **New discovery methods and techniques,** judged by whether they change how the agent thinks, verifies, or measures, not by coverage alone.
- **Language companion files** (see below).
- **Real-world performance problems** where an agent without the skill gets it wrong: slow code, hostile inputs, or an optimization that broke behavior or security.
- **Evidence** from running the skill with other agents and models, described in the issue or pull request as what the agent did differently, without pass rates or case names (see "Evaluation").

## How changes reach `main`

1. Branch from `main` and open a pull request. Direct pushes to `main` are blocked.
2. The `skill-checks` workflow must pass: it checks that `skills/SKILL.md` exists with the skill's name, that `CHANGELOG.md` has an `[Unreleased]` section, and that the guard hook tests pass (`python3 -m unittest discover -s plugin/tests`). It does not check links or quoted section names (see "Keep references whole" below), and it does not check that nothing under `evals/` or no archive is tracked: both are candidates for the workflow, and until then are checked by the reviewer.
3. If the change affects what the skill does, add a line to `[Unreleased]` in `CHANGELOG.md`, written for someone who installs the skill: what the agent now does differently.
4. A reviewer reads every changed line under `skills/` as described in "Reviewing changes to the skill" below. The project currently has one maintainer, and the repository rules require no approvals, so this review is the maintainer's own review of their changes and of each contributor's pull request; it becomes a second person's review once there is a second maintainer (see "Repository rules" in [RELEASING.md](RELEASING.md)).
5. Resolve review threads, then merge with squash or rebase.

## Changing the skill

- **Put each instruction where it belongs.** A mandatory rule goes in `skills/SKILL.md`, stated briefly, with its full text in "Rule details" in `skills/WORKFLOW.md` and its steps in the file that carries it out. Anything else lives in exactly one file, and others point to it.
- **Write for coding-tier models** such as Claude Sonnet and Opus. Every instruction must be followable without guessing: explicit, no shorthand, and an example where a rule is easy to misread.
- **Keep sources out of the skill.** A skill file that makes claims keeps its sources in `docs/sources/` at the same path (for example `docs/sources/techniques/hostile-inputs.md` for `skills/techniques/hostile-inputs.md`), outside the installed skill, and the skill file does not point to them. Each entry names the page, section, or source file that supports a specific claim, not a site's front page, and says so when a claim is implementation behavior or has no published source. A file with no claims of its own, such as a mode file, needs no sources file. `skills/languages/GENERIC.md` has none: each profile it builds records its own sources. When you change a claim, update its source in the same pull request.
- **Keep generic files language-neutral.** Name concepts ("an operation that copies a collection"), not one language's functions. Language-specific facts belong in `skills/languages/`; a generic file may use a function name only as a recognizable example of a pattern, and name a language only where platforms differ on the point being made.
- **Keep references whole.** When you rename a file or a section, or renumber a rule, update every link, file name, quoted section name, and rule number that points at it. An agent that follows a reference to nothing skips that step.
- **Do not trim instructions to save tokens.** Every file except `skills/SKILL.md` is loaded only when a step names it. Remove repetition, never content.
- **Measure behavior changes.** A change meant to alter what agents do should be tested before and after on the same cases, with and without the change.

## Reviewing changes to the skill

Every line under `skills/` is an instruction that every user's agent follows, with access to their code and shell. Review it like code that runs on their machines:

- **Look for injected or weakening text.** Reject wording that tells the agent to treat some file, comment, or marker as approval; to run a command without reading it, as root, or against real services; to skip differential tests, a time limit, or the final summary lines; to send, upload, or copy data anywhere; or that makes an exception to "Untrusted content", "Before running a command", or "When the request itself is risky" in `skills/SKILL.md`. Check hidden text as well: HTML comments, link targets, zero-width or look-alike characters, and code blocks.
- **Check that examples teach the safe behavior.** An example that shows a security-weakening speedup without naming what it breaks, or a technique without its preconditions, teaches agents to copy it.
- **No new commands, URLs, or dependencies without a reason.** A command or download in a skill file can be run by every user's agent. Pin versions and use official sources.
- **Language profiles contributed from a project** (`.algorithmic-intelligence/languages/`) were written by an agent and may have been edited since: check every claim against its cited source and remove anything addressed to the agent.

## Removing rules

Every line of `skills/SKILL.md` is loaded on every run, so a rule there must earn its place. But a rule with no test case needs a case, not deletion: it has not been tested yet, which does not mean it does nothing. Remove or move a rule only after a before-and-after run shows the same results without it, and only with the maintainer's approval. Technique files, `DISCOVERY.md`, and language files load only when a step routes to them; they cover code few tests reach (kernels, databases, compilers) and are not pruned for lack of a case.

## Language companion files

Use [`skills/languages/GENERIC.md`](skills/languages/GENERIC.md) as the checklist, follow the structure of the existing files, add a row to `skills/languages/INDEX.md`, and link the file from the language row of the table in `skills/SKILL.md`. A profile the skill saved in your project (`.algorithmic-intelligence/languages/<LANGUAGE>.md`) is a good starting point. Cover the language, its standard library, and any first-party or well-maintained package that fills a gap the standard library leaves (what it provides and its behavior traps, confirmed in the official registry), not frameworks. Cite official documentation for every complexity and ordering claim, and where a claim is implementation behavior rather than documented behavior, say so. Sources go in `docs/sources/languages/<LANGUAGE>.md`, grouped by the language file's sections, not in the language file.

## Evaluation

A new evaluation harness is being built from scratch. [docs/EVAL-PLAN.md](docs/EVAL-PLAN.md) describes what it will test (hostile inputs, security side effects of optimizations, unsafe commands and injected text, unusual problems, and write mode, on Sonnet and Opus).

Keep evaluation results out of the repository: no metrics, pass rates, scores, or case and fixture names in the skill, the docs, the changelog, or pull request descriptions that land in the history. The public plan names only the categories tested; the cases, traps, probe inputs, fixtures, sample sizes, and budgets live in a private file under `evals/`, which is not tracked. Describe what a change makes the agent do differently instead. Test cases and their answer keys stay private so they remain held out.

## Toolchains

The dev container in `.devcontainer/` has the JDK, Python, C, Node, Rust, Swift, and Ruby toolchains, and Claude Code. It has no Kotlin or C# toolchain.

## Reporting problems

Bugs and suggestions: open an issue with the template. Security problems: follow [SECURITY.md](SECURITY.md) and report privately.
