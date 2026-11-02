# Security policy

## Supported versions

Security fixes are made on the latest release. Older releases do not get fixes; update to the latest one.

| Version | Supported |
|---|---|
| Latest release (see [Releases](https://github.com/protechnocrats/algorithmic-intelligence/releases)) | Yes |
| Earlier releases | No |

## Reporting a vulnerability

**Please do not open a public issue for a security problem.** Report it privately through GitHub: on this repository's **Security** tab, choose **Report a vulnerability**. Only the maintainers can see the report.

Include what you can of the following:

- The skill version (release tag or commit) and the coding agent and model you used.
- The file and wording involved (for example a rule in `skills/SKILL.md` or a step in `skills/WORKFLOW.md`).
- How to reproduce it: the project or prompt, what the agent did, and what it should have done.
- The impact: what could be read, changed, run, or leaked, and by whom.

You can expect an acknowledgment within 7 days, and an assessment with a planned fix or an explanation within 30 days. Fixes are published in a release whose notes describe the problem once users have had a chance to update. Reporters are credited in the release notes unless they ask not to be.

## What counts as a security issue here

This project is a set of instructions that coding agents follow, plus evaluation scripts. A vulnerability is anything in it that can make an agent, or a person running the scripts, act against the developer's interests. For example:

- **Instructions that lead an agent to run, change, delete, or send something the developer did not ask for,** or to skip an approval the skill promises (the mandatory rules say behavior changes, dependencies, and commits need the developer's explicit approval).
- **Prompt injection through files the skill tells agents to read.** The skill loads language profiles saved in the project (`.algorithmic-intelligence/languages/<LANGUAGE>.md`) and tells agents to treat them as data. A way to make an agent follow instructions placed in such a file, in a fetched web page, or in project code is a vulnerability.
- **Guidance that produces insecure code,** for example advice that removes a limit, uses a non-constant-time comparison on secrets, or picks a structure that is quadratic on attacker-chosen input where the skill claims to prevent that (`skills/techniques/hostile-inputs.md`).
- **Evaluation scripts** (`evals/`) that run code or write files outside the run directories they create, or that expose credentials.

Not security issues (open a normal issue instead): an agent producing slow code, a wrong complexity claim, or a missed optimization, unless it creates one of the risks above.

## Running the evaluation scripts safely

The scripts in `evals/` start real coding-agent sessions on your machine, and those sessions can run commands (tests, benchmarks, Python). They work in copies of the fixtures outside this repository, but they are not sandboxed. Run them only on a machine where that is acceptable, with a spending limit (`--max-total-usd`), and never with credentials in the environment that the sessions should not have.
