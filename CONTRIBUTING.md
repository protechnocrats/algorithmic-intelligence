# Contributing

Thank you for helping. This project is a skill: Markdown instructions that coding agents follow. Read [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) first. It shows which file holds what, and what an agent loads when.

## What helps most

- **New discovery methods and techniques,** judged by whether they change how the agent thinks, verifies, or measures, not by coverage alone.
- **Language companion files** (see below).
- **Real-world performance problems** where an agent without the skill gets it wrong: slow code, hostile inputs, or an optimization that broke behavior or security.
- **Evidence** from running the skill with other agents and models.

## How changes reach `main`

1. Branch from `main` and open a pull request. Direct pushes to `main` are blocked.
2. The `skill-checks` workflow must pass: it checks the skill's name and layout, and that `CHANGELOG.md` has an `[Unreleased]` section.
3. If the change affects what the skill does, add a line to `[Unreleased]` in `CHANGELOG.md`, written for someone who installs the skill: what the agent now does differently.
4. Resolve review threads, then merge with squash or rebase.

## Changing the skill

- **Put each instruction where it belongs.** A mandatory rule goes in `skills/SKILL.md` and in the file that carries it out. Anything else lives in exactly one file, and others point to it.
- **Write for coding-tier models.** The skill is tested with Claude Sonnet and Opus. Every instruction must be followable without guessing: explicit, no shorthand, and an example where a rule is easy to misread.
- **Keep generic files language-neutral.** Name concepts ("an operation that copies a collection"), not one language's functions. Language-specific names belong in `skills/languages/`.
- **Keep references whole.** When you rename a file or a section, or renumber a rule, update every link, file name, quoted section name, and rule number that points at it. An agent that follows a reference to nothing skips that step.
- **Do not trim instructions to save tokens.** Every file is loaded only when a step names it. Remove repetition, never content.
- **Measure behavior changes.** A change meant to alter what agents do should be tested before and after on the same cases, with and without the change.

## Removing rules

Every line of `skills/SKILL.md` is loaded on every run, so a rule there must earn its place. But a rule with no test case needs a case, not deletion: it has not been tested yet, which does not mean it does nothing. Remove or move a rule only after a before-and-after run shows the same results without it, and only with the maintainer's approval. Technique files, `DISCOVERY.md`, and language files load only when a step routes to them; they cover code few tests reach (kernels, databases, compilers) and are not pruned for lack of a case.

## Language companion files

Use [`skills/languages/GENERIC.md`](skills/languages/GENERIC.md) as the checklist, follow the structure of the existing files, and add a row to `skills/languages/INDEX.md`. A profile the skill saved in your project (`.algorithmic-intelligence/languages/<LANGUAGE>.md`) is a good starting point. Cover the language and its standard library only, not frameworks. Cite official documentation for every complexity and ordering claim, and where a claim is implementation behavior rather than documented behavior, say so.

## Evaluation

The evaluation harness is being rebuilt. [docs/EVAL-PLAN.md](docs/EVAL-PLAN.md) describes what it will test (hostile inputs, security side effects of optimizations, unusual problems, and write mode, on Sonnet and Opus). Earlier rounds and their tooling are in the git history before the `evals/` folder was removed.

## Toolchains

The dev container in `.devcontainer/` has the JDK, Ruby, Node, Rust, Python, and Swift toolchains.

## Reporting problems

Bugs and suggestions: open an issue with the template. Security problems: follow [SECURITY.md](SECURITY.md) and report privately.
