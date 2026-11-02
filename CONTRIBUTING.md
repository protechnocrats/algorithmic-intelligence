# Contributing

Thank you for helping. This project is a skill (Markdown instructions that coding agents follow) plus the evaluations that measure it. Read [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) first: it shows which file holds what and what an agent loads when.

## What helps most

- **New discovery methods and techniques,** judged by whether they change how the agent thinks, verifies, or measures, not by coverage alone.
- **Language companion files** (see below).
- **Evaluation cases,** especially ones where an agent without the skill is likely to fail, and real-world performance problems.
- **Evidence:** runs of the evals on other agents and models.

## How changes reach `main`

1. Branch from `main` and open a pull request. Direct pushes to `main` are blocked.
2. The `skill-checks` workflow must pass: skill name and layout, token budgets, eval scripts parse, `CHANGELOG.md` has an `[Unreleased]` section.
3. If the change affects what the skill does, add a line to `[Unreleased]` in `CHANGELOG.md`, written for someone who installs the skill: what the agent now does differently.
4. Resolve review threads; merge with squash or rebase.

## Changing the skill

- **Put each instruction where it belongs.** A mandatory rule goes in `skills/SKILL.md` and in the file that carries it out; anything else lives in exactly one file, and others point to it.
- **Write for the weakest agent.** Every instruction must be followable by a small model without guessing: explicit, no shorthand, examples where a rule is easy to misread.
- **Keep generic files language-neutral.** Name concepts ("an operation that copies a collection"), not one language's functions; language-specific names belong in `skills/languages/`.
- **Run `evals/token-budget.sh`.** If a needed instruction exceeds a budget, raise the budget in the script with the reason. Never shorten or move instructions to fit.
- **Measure behavior changes.** A change meant to alter what agents do should be tested before and after on a tuning fixture (see `evals/README.md`), never tuned on a held-out fixture.

## Language companion files

Use [`skills/languages/GENERIC.md`](skills/languages/GENERIC.md) as the checklist, follow the structure of the existing files, and add a row to `skills/languages/INDEX.md`. A profile the skill saved in your project (`.algorithmic-intelligence/languages/<LANGUAGE>.md`) is a good starting point. Cover the language and its standard library only, not frameworks. Cite official documentation for every complexity and ordering claim. Where a claim is implementation behavior rather than documented behavior, say so, and add a check under `evals/claims/` (see `evals/claims/kotlin/`).

## Evaluation cases

Follow "Adding a case" in [evals/README.md](evals/README.md). Every case states, before any run, why an agent without the skill is likely to fail it; invented problems need their intended answer checked against a brute-force reference; probe checks are confirmed against a correct rewrite and the tempting wrong one (add both to `evals/probes/selftest/`).

## Running things

- **Free:** `evals/token-budget.sh`, `evals/selftest.sh` (the harness, with a stub agent), `evals/selftest.sh --probes` (the graders), the fixtures' own test suites, `evals/claims/kotlin-claims.sh`.
- **Costs money:** `evals/run-pilot.sh` and `evals/trigger-test.sh` start real agent sessions. Always pass `--max-total-usd`, and read [SECURITY.md](SECURITY.md) on running them safely.
- **Toolchains:** the dev container in `.devcontainer/` has the JDK, Ruby, Node, Rust, Python, and Swift the fixtures need.

## Reporting problems

Bugs and suggestions: open an issue with the template. Security problems: follow [SECURITY.md](SECURITY.md) and report privately.
