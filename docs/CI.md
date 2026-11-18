# Pull request review in CI

The repository is also a GitHub Action. On every pull request it runs the skill in report mode on the code the pull request changes and posts one comment, which it updates on each new push. The comment follows the skill's final summary: the result first, decisions needed, a table of findings with the complexity before and after, bugs and hazards noticed, and the test or benchmark that would confirm each finding. It edits nothing and runs nothing, so every number in it is an estimate read from the code, and the comment says so. The comment is written by an AI model (Claude, through Claude Code) and says that too: it can be wrong, so read it as a reviewer's suggestions, not as a verdict.

Available from release 0.7.2; the AI disclosure and the report link in the comment are from 0.7.3.

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
| `review-drafts` | `false` | Review draft pull requests too. |
| `claude-code-version` | pinned | Claude Code version installed from npm. |
| `github-token` | `github.token` | Token used to post the comment. |

## What it skips

- Pull requests that change only documentation, images, licenses, or lock files.
- Draft pull requests, unless `review-drafts` is `true`.
- Pull requests from forks. GitHub does not give workflows triggered by a fork's pull request the repository's secrets, so there are no model credentials; the run says so and passes. Do not work around this with `pull_request_target`: that trigger runs with the secrets and a write token, and checking out a fork's code in it hands both to code you have not reviewed.

A review that fails (budget reached, timeout, authentication error) posts a comment saying so and does not fail the check, so it never blocks a merge. To make it required, check the comment yourself; the action does not gate merges.

## Security model

The pull request under review is untrusted: its code, comments, and documentation can contain instructions aimed at the agent. The action limits what such instructions can achieve.

- **The agent can only read.** Claude Code runs with `--restricted` and only the Read, Grep, Glob, and Skill tools: no shell, no file edits, no web access, and no MCP servers. Restricted mode also confines reading to the checkout and the action's work directory, and ignores the repository's Claude Code settings and hooks. The agent cannot run the project's code, its tests, or its build scripts.
- **Credentials are split across steps.** The step that runs the agent has the model credentials and no GitHub token. The step that posts the comment has the GitHub token and no model credentials. With `persist-credentials: false`, the token is not in `.git/config` either.
- **The comment is cleaned before posting.** Mentions are neutralized so the comment cannot notify people, the length is capped, and the action only ever edits a comment written by a bot that carries its marker.
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
