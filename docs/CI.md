# Pull request review in CI

The repository is also a GitHub Action. On every pull request it runs the skill in report mode on the code the pull request changes and posts one comment, which it updates on each new push. The comment follows the skill's final summary: the result first, decisions needed, a table of findings with the complexity before and after, bugs and hazards noticed, and the test or benchmark that would confirm each finding. It edits nothing and runs nothing, so every number in it is an estimate read from the code, and the comment says so. The comment is written by an AI model (Claude, through Claude Code) and says that too: it can be wrong, so read it as a reviewer's suggestions, not as a verdict.

Available from release 0.7.2; the AI disclosure and the report link in the comment are from 0.7.3. Review comments on changed lines, the comparison with the last review, quiet clean reviews, step outputs, skipping unchanged code, and fork support are unreleased (see the changelog).

## Setup

1. Add a repository secret: `ANTHROPIC_API_KEY` (an Anthropic API key), or `CLAUDE_CODE_OAUTH_TOKEN` (from `claude setup-token`, to use a Claude subscription).
2. Add a workflow to your repository, for example as performance-review.yml in .github/workflows:

```yaml
name: performance review

on:
  pull_request:
    types: [opened, synchronize, reopened, ready_for_review]

permissions:
  contents: read
  pull-requests: write

concurrency:
  group: performance-review-${{ github.event.pull_request.number }}
  cancel-in-progress: true

jobs:
  review:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1  # v7.0.1
        with:
          fetch-depth: 0               # the review diffs against the base commit
          persist-credentials: false   # keeps the GitHub token out of .git/config, which the agent can read
      - uses: protechnocrats/algorithmic-intelligence@0.7.3
        with:
          anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}
          # claude-code-oauth-token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
          instructions: |
            Production sizes: orders table about 5M rows, 2,000 requests per second on /orders.
            Batch import files up to 2 GB.
```

The `instructions` are the most useful input: production input sizes and latency targets let the review say whether a finding matters at your scale instead of guessing.

## Inputs

| Input | Default | Meaning |
|---|---|---|
| `anthropic-api-key` | | Anthropic API key. Give this or `claude-code-oauth-token`. |
| `claude-code-oauth-token` | | Claude Code OAuth token, for a Claude subscription. |
| `model` | `sonnet` | Model alias or full name. Empty uses Claude Code's default. |
| `max-budget-usd` | `2` | The review stops once it has spent this much. |
| `timeout-minutes` | `20` | The review stops after this long. |
| `max-diff-kb` | `200` | Larger diffs are cut at a file boundary; the agent reads the changed files for the rest. |
| `instructions` | | Production sizes, latency targets, and constraints, passed to the reviewer. |
| `comment` | `true` | When `false`, the report goes only to the job summary. |
| `comment-on-clean` | `false` | Post a comment when the review finds nothing. When `false`, a clean review goes only to the job summary, and an earlier comment is updated to say its findings are gone. |
| `inline-comments` | `true` | Also post new findings as review comments on the changed lines they concern. |
| `max-inline-comments` | `10` | At most this many review comments on changed lines per push, highest severity first. |
| `inline-min-severity` | `medium` | Lowest severity posted on the changed lines (`high`, `medium`, or `low`); lower findings stay in the comment. |
| `review-drafts` | `false` | Review draft pull requests too. |
| `allow-forks` | `false` | Review pull requests from forks (see "Pull requests from forks"). |
| `fork-authors` | `OWNER,MEMBER,COLLABORATOR` | Author associations whose fork pull requests are reviewed when `allow-forks` is `true`. |
| `fork-label` | | A label a maintainer adds to have any fork pull request reviewed when `allow-forks` is `true`. |
| `claude-code-version` | pinned | Claude Code version installed from npm. |
| `github-token` | `github.token` | Token used to post the comment. |

## What a review gives you

- **One comment, updated on each push.** The report, with a line at the top comparing it with the previous review: how many findings are new, still present, and resolved, and which were resolved.
- **Review comments on the changed lines.** Each new finding of at least `inline-min-severity` (medium by default) that points at a line the pull request changes is also posted on that line, highest severity first, up to `max-inline-comments`. Findings repeated from an earlier review are not posted again.
- **Quiet when there is nothing to say.** A review that finds nothing posts no comment unless `comment-on-clean` is `true`; the job summary still has it. If an earlier comment listed findings, it is updated to say they are gone.
- **Outputs for the rest of your workflow.** `status` (`reviewed`, `failed`, `skipped`, or `unchanged`), `findings`, `high`, `medium`, `low`, `clean`, and `resolved`. The counts are empty when the review gave no machine-readable findings. For example, to fail the check on a high-severity finding (the action itself never fails it):

```yaml
      - uses: protechnocrats/algorithmic-intelligence@<tag>
        id: review
        with:
          anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}
      - if: steps.review.outputs.high != '' && steps.review.outputs.high != '0'
        run: echo "High-severity performance finding; see the review comment." && exit 1
```

Every finding is an estimate read from the code, so a gate like this is a judgment call: it stops merges on a reviewer's opinion, not on a measurement.

The reviewer is given the pull request's title and description (as the author's claims, checked against the code), the start of the top-level README and the repository's documentation files by name, and the maintainers' `instructions`, so it can find production sizes before estimating any.

## What it skips

- Pull requests that change only documentation, images, licenses, or lock files.
- Draft pull requests, unless `review-drafts` is `true`.
- Pushes that leave the code unchanged since the last review: documentation edits, a clean rebase, or a re-run. The comment records a fingerprint of the pull request's code changes, the `instructions`, and the action version, and a push with the same fingerprint is not reviewed again (the `status` output is `unchanged`, and the counts repeat the last review's). A clean review that posted no comment leaves no fingerprint, so its next push is reviewed again.
- Pull requests from forks, unless you set them up as described below. GitHub does not give workflows triggered by a fork's pull request (`pull_request`) the repository's secrets, so there are no model credentials; the run says so and passes.

A review that fails (budget reached, timeout, authentication error) posts a comment saying so and does not fail the check, so it never blocks a merge. To make it required, check the comment yourself; the action does not gate merges.

## Pull requests from forks

Reviewing a fork's pull request needs the `pull_request_target` trigger, which runs the workflow from your base branch with your secrets and a write token. That trigger is dangerous when a workflow runs the pull request's code: a build, a test, an install script. This action runs none of it: the scripts it runs come from the action's own pinned release, and the agent can only read files. Even so, set it up exactly like this, in a workflow of its own, with no other steps:

```yaml
name: performance review

on:
  pull_request_target:
    types: [opened, synchronize, reopened, ready_for_review, labeled]

permissions:
  contents: read
  pull-requests: write

concurrency:
  group: performance-review-${{ github.event.pull_request.number }}
  cancel-in-progress: true

jobs:
  review:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1  # v7.0.1
        with:
          ref: ${{ github.event.pull_request.head.sha }}   # the pull request's code, to read, never to run
          fetch-depth: 0
          persist-credentials: false
      - uses: protechnocrats/algorithmic-intelligence@<tag>
        with:
          anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}
          allow-forks: true
          fork-label: performance-review
```

This one workflow reviews pull requests from branches in your repository too, so it replaces the `pull_request` workflow rather than joining it.

- **Who gets reviewed.** A fork's pull request is reviewed only when its author's association is in `fork-authors` (by default owners, organization members, and collaborators), or when a maintainer adds `fork-label`. Anyone else's pull request is skipped, so strangers cannot spend your API budget; adding the label after reading the pull request is the way to review one.
- **Never add a step that runs the checked-out code** (a build, tests, `npm install`, a cache restore keyed on its files) to this workflow. That is what makes `pull_request_target` dangerous, and nothing in this action can protect you from it.
- **The action checks the setup.** It stops if the checkout is not the pull request's code, or if the checkout kept the GitHub token in `.git/config`.

## Security model

The pull request under review is untrusted: its code, comments, and documentation can contain instructions aimed at the agent. The action limits what such instructions can achieve.

- **The agent can only read.** Claude Code runs with `--restricted` and only the Read, Grep, Glob, and Skill tools: no shell, no file edits, no web access, and no MCP servers. Restricted mode also confines reading to the checkout and the action's work directory, and ignores the repository's Claude Code settings and hooks. The agent cannot run the project's code, its tests, or its build scripts.
- **Credentials are split across steps.** The step that runs the agent has the model credentials and no GitHub token. The steps that prepare the review (reading the previous comment) and post it have the GitHub token and no model credentials. With `persist-credentials: false`, the token is not in `.git/config` either, and the action refuses to run if it is.
- **What the agent writes is cleaned and checked before posting.** Mentions are neutralized so nothing it writes can notify people, the length is capped, and the action only ever edits a comment written by a bot that carries its marker. The machine-readable findings are validated field by field, and a review comment goes only on a line the pull request changes.
- **What remains.** A pull request can change the repository's `CLAUDE.md`, skills, or code comments to steer what the review says, for example to hide a finding. Treat the comment as advice from a reviewer who read the pull request, not as a security control.

The action itself is pinned by its release tag, and release tags in this repository cannot be moved (see [RELEASING.md](../RELEASING.md)). For the strongest guarantee, pin it by commit SHA instead.

## Data

- **What is sent, and to whom.** The review runs on your GitHub runner. Claude Code sends the prompt, the pull request's diff, and the files the agent reads in your repository to Anthropic's API, under the API key or subscription you provide and Anthropic's terms for it. Nothing else leaves the runner, apart from the comment posted to your pull request through GitHub's API.
- **What the maintainers receive.** Nothing. The action has no telemetry and sends nothing to the maintainers of this project or to any service other than Anthropic's API and GitHub's.
- **What is kept.** The action keeps no session history on the runner (`--no-session-persistence`), and the runner's work directory is discarded when the job ends. The comment and the job summary stay on GitHub like any other comment. Retention of what Anthropic receives is set by your agreement with Anthropic.
- **Personal data.** The action does not look for personal data, but code, comments, and test fixtures can contain some (names, email addresses). If your repository holds data that must not go to a third-party model, do not enable the action on it.

## Support and feedback

- **A wrong, misleading, or harmful review:** open an issue at [github.com/protechnocrats/algorithmic-intelligence/issues](https://github.com/protechnocrats/algorithmic-intelligence/issues); every comment links there ("Report a problem"). Include the run link from the comment, and leave out code you cannot share.
- **A security problem in the action:** report it privately, as described in [SECURITY.md](../SECURITY.md); do not open a public issue.
- **Anything else:** contactus@protechnocrats.com.

The action is provided under the [MIT License](../LICENSE), without warranty.

## Cost

Each review is one Claude Code session over the changed code and the files around it. `max-budget-usd` caps it; `concurrency` in the workflow above cancels a review when a newer push arrives, so only the latest commit is paid for. API usage is billed to the key or subscription you provide.

## Limits

- Report only. Nothing is measured, so findings are estimates to confirm with the benchmark each one names. Apply mode, which would open a pull request with a verified fix, is not part of the action.
- GitHub-hosted Linux runners, or self-hosted runners with Node.js, npm, Python 3, and git.
- The skill's evaluation (see [RESULTS.md](RESULTS.md)) measured interactive sessions that could run code, not this read-only review.
- Severity is the reviewer's judgment from the stated sizes, and line numbers are its reading of the file; a finding whose line is not in the diff stays in the comment only.
