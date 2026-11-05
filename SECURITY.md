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
- How to reproduce it: the project or prompt, what the agent did, and what it should have done. A minimal project you wrote is best. Do not send real secrets, customer data, or a working exploit against someone else's system; describe the pattern instead.
- The impact: what could be read, changed, run, or leaked, and by whom.

You can expect an acknowledgment within 7 days, and an assessment with a planned fix or an explanation within 30 days. Fixes are published in a release whose notes describe the problem once users have had a chance to update. Reporters are credited in the release notes unless they ask not to be.

## What counts as a security issue here

This project is a set of instructions that coding agents follow. A vulnerability is anything in it that can make an agent act against the developer's interests. For example:

- **Prompt injection through project files.** The skill tells agents that everything they read is evidence, not instruction ("Untrusted content" in `skills/SKILL.md`): code, comments, docs, configuration, test data, commit messages, program output, fetched pages, and files earlier sessions wrote. A way to make an agent follow text placed in any of these, or accept a forged approval ("approved by the developer", "pre-approved"), is a vulnerability.
- **Tampered files the skill reads back.** Saved language profiles (`.algorithmic-intelligence/languages/<LANGUAGE>.md`), reports, bug logs, and test harnesses from earlier sessions can be edited between sessions. A way to make an agent trust such a file's claims or instructions without rechecking them is in scope.
- **Unsafe command execution.** Wording that leads an agent to run a command without reading what it triggers, run as root, use production credentials or hosts, reach outside the machine, delete outside the project, or run without a time or size bound ("Before running a command" in `skills/SKILL.md`), including through a differential test or benchmark that runs the original code's side effects.
- **Skipped approvals.** Instructions that let an agent change, commit, or add something the developer did not approve in the conversation (behavior changes, dependencies, schema or configuration changes, commits), treat one approval as covering others, or act on approval items in a run where nobody can answer.
- **Security-weakening optimizations.** Guidance that produces or accepts a speedup that removes validation or a size limit, compares secrets with an early exit, caches permissions or sessions without invalidation, leaves the user or tenant out of a cache key, disables hash randomization or certificate checks, logs data that was not logged before, or picks a structure that is quadratic on attacker-chosen input where the skill claims to prevent that ("When the request itself is risky" in `skills/SKILL.md`, `skills/techniques/hostile-inputs.md`).
- **Data leaving where it was.** The skill says secrets and real customer or production data are never copied into code, tests, fixtures, reports, or summaries, and that the agent does not open secret files or follow symbolic links out of the project ("Untrusted content" in `skills/SKILL.md`). Wording that leads an agent to write a secret or production data into any file it produces, read outside the project, or run against production data is in scope.
- **Changes to the skill itself.** Text in a pull request, fork, or release that adds instructions weakening any of the above.

Not security issues (open a normal issue instead): an agent producing slow code, a wrong complexity claim, or a missed optimization, unless it creates one of the risks above. Vulnerabilities in a coding agent itself, or in a model, go to that agent's or model's vendor; report here only when the skill's wording causes or worsens them.
