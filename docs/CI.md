# Pull request review in CI

The repository is also a GitHub Action. On every pull request it runs the skill in report mode on the code the pull request changes and posts one comment, which it updates on each new push. The comment follows the skill's final summary: the result first, decisions needed, a table of findings with the complexity before and after, bugs and hazards noticed, and the test or benchmark that would confirm each finding. It edits nothing and runs nothing, so every number in it is an estimate read from the code, and the comment says so. The comment is written by an AI model (Claude, through Claude Code) and says that too: it can be wrong, so read it as a reviewer's suggestions, not as a verdict.

Available from release 0.7.2; the AI disclosure and the report link in the comment are from 0.7.3. Review comments on changed lines, the comparison with the last review, quiet clean reviews, step outputs, skipping unchanged code, and fork support are from 0.7.4; `comment-min-severity` is from 0.7.5. The configuration file, `exclude-paths`, `require-label`, `/algo-intelligence` commands and dismissals, replies on review threads, blocking on findings (`block-on-severity`), SARIF, Amazon Bedrock and Google Vertex AI, and the integrity-checked install are unreleased (in the development version).

## Setup

1. Add a repository secret: `ANTHROPIC_API_KEY` (an Anthropic API key), or `CLAUDE_CODE_OAUTH_TOKEN` (from `claude setup-token`, to use a Claude subscription).
2. Add a workflow to your repository, for example as algorithmic-intelligence.yml in .github/workflows:

```yaml
name: Algorithmic Intelligence

on:
  pull_request:
    types: [opened, synchronize, reopened, ready_for_review]

permissions:
  contents: read
  pull-requests: write

concurrency:
  group: algorithmic-intelligence-${{ github.event.pull_request.number }}
  cancel-in-progress: true

jobs:
  review:
    name: Algorithmic Intelligence - review
    if: github.event.pull_request.draft == false   # drafts are not reviewed; marking one ready reviews it
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1  # v7.0.1
        with:
          fetch-depth: 0               # the review diffs against the base commit
          persist-credentials: false   # keeps the GitHub token out of .git/config, which the agent can read
      - uses: protechnocrats/algorithmic-intelligence@0.7.5
        with:
          anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}
          # claude-code-oauth-token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
          instructions: |
            Production sizes: orders table about 5M rows, 2,000 requests per second on /orders.
            Batch import files up to 2 GB.
```

Production sizes and latency targets are the most useful thing you can give the reviewer: they let it say whether a finding matters at your scale instead of guessing. Put them in `instructions`, or in a file the action reads from the base branch, `.github/algorithmic-intelligence.md` by default (`config-file`), so they live in the repository with the code:

```markdown
Production sizes: orders table about 5M rows, 2,000 requests per second on /orders, p95 target 200 ms.
Batch import files up to 2 GB. Internal tools under tools/ run by hand, rarely.
```

The file is read from the base commit, never from the pull request, so a pull request cannot change what the reviewer is told; an edit to it takes effect once merged. Its text and `instructions` are both given to the reviewer.

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
| `provider` | `anthropic` | `anthropic`, `bedrock` (Amazon Bedrock), or `vertex` (Google Vertex AI); see "Other model providers". |
| `aws-region` | | AWS region for `bedrock` (empty uses `AWS_REGION` from the job). |
| `vertex-project-id` | | Google Cloud project for `vertex`. |
| `vertex-region` | | Vertex AI region for `vertex`, such as `us-east5` or `global`. |
| `config-file` | `.github/algorithmic-intelligence.md` | Sizes, targets, and constraints for the reviewer, read from the base branch. Empty disables. |
| `exclude-paths` | | Glob patterns of files not to review (generated, vendored), one per line or comma separated. `*` matches across directories; a directory pattern such as `vendor/` covers everything under it. |
| `require-label` | | Review only pull requests carrying this label. Add `labeled` to the workflow's `pull_request` types. |
| `command-authors` | `OWNER,MEMBER,COLLABORATOR` | Author associations whose `/algo-intelligence` comments are obeyed. |
| `reply-to-threads` | `true` | Reply on this action's review threads when their finding is fixed or dismissed; the developer resolves them. |
| `fail-on-error` | `true` | Fail the job when the review does not finish. `false` lets such a run pass. |
| `block-on-severity` | `high` | Fail the job on a finding at or above this severity (`high`, `medium`, or `low`) until it is fixed or dismissed. Empty never fails on findings. See "Blocking merges". |
| `sarif` | `false` | Also write the findings as SARIF for code scanning (see "Code scanning"). |
| `comment` | `true` | When `false`, the report goes only to the job summary. |
| `comment-on-clean` | `false` | Post a comment when the review finds nothing. When `false`, a clean review goes only to the job summary, and an earlier comment is updated to say its findings are gone. |
| `comment-min-severity` | `medium` | A review whose findings are all below this severity (`high`, `medium`, or `low`) posts no new comment, as if clean. Set `low` for a comment on every finding. |
| `inline-comments` | `true` | Also post new findings as review comments on the changed lines they concern. |
| `max-inline-comments` | `10` | At most this many review comments on changed lines per push, highest severity first. |
| `inline-min-severity` | `medium` | Lowest severity posted on the changed lines (`high`, `medium`, or `low`); lower findings stay in the comment. |
| `review-drafts` | `false` | Review draft pull requests too. |
| `allow-forks` | `false` | Review pull requests from forks (see "Pull requests from forks"). |
| `fork-authors` | `OWNER,MEMBER,COLLABORATOR` | Author associations whose fork pull requests are reviewed when `allow-forks` is `true`. |
| `fork-label` | | A label a maintainer adds to have any fork pull request reviewed when `allow-forks` is `true`. |
| `claude-code-version` | pinned | Claude Code version installed from npm. The release's version is installed from a lockfile that checks the integrity hash of every download; another version is installed without that check, with a warning. |
| `github-token` | `github.token` | Token used to post the comment. |

## What a review gives you

- **One comment, updated on each push.** The report, with a line at the top comparing it with the previous review: how many findings are new, still present, and resolved, and which were resolved.
- **Review comments on the changed lines.** Each new finding of at least `inline-min-severity` (medium by default) that points at a line the pull request changes is also posted on that line, highest severity first, up to `max-inline-comments`. Findings repeated from an earlier review are not posted again.
- **Quiet when there is nothing to say.** A review that finds nothing, or only findings below `comment-min-severity` (medium by default), posts no new comment unless `comment-on-clean` is `true`; the job summary and the outputs still have its findings. If an earlier comment exists, it is updated: to say its findings are gone, or with the new report.
- **Threads that say when they are done.** When a push fixes a finding, its review comment gets a reply saying so, and a dismissed finding's comment gets one naming who dismissed it (`reply-to-threads`). The action leaves the conversation open for the developer to resolve, so resolving it records that a person read the outcome; it needs no more than `pull-requests: write`.
- **A failed run keeps the last report.** When a review does not finish (budget, timeout, an API error), the comment keeps the last report that did, with a note on top saying the latest run failed, so a transient error never wipes useful findings.
- **Outputs for the rest of your workflow.** `status` (`reviewed`, `failed`, `skipped`, or `unchanged`), `findings`, `high`, `medium`, `low`, `clean`, `resolved`, `blocked`, and `sarif-file`. The counts are empty when the review gave no machine-readable findings.
- **A red check on blocking findings.** See "Blocking merges".

## Blocking merges

The job fails when the review has a finding at or above `block-on-severity` (`high` by default), so the pull request shows one red check, **Algorithmic Intelligence - review**, with the findings in the comment. Choose the severity with `block-on-severity`: `high` fails only on findings that would miss the stated targets or degrade badly at production sizes, `medium` and `low` fail on more, and an empty value never fails on findings.

On its own a red check is a warning anyone can merge past. To make it a real block, add **Algorithmic Intelligence - review** as a required status check in a branch rule (Settings → Rules, or branch protection).

A maintainer who disagrees with a finding comments `/algo-intelligence dismiss P1`. With the command workflow above (it needs `actions: write`), the dismissal re-runs the failed job at once; the re-run finds the code unchanged, runs no model, so it costs no API usage, and passes if nothing else blocks. Without the command workflow, the dismissal is picked up by the next push, or by re-running the job yourself. A draft pull request is not reviewed, so a required check waits until it is marked ready.

Every finding is an estimate read from the code, so blocking is a judgment call: it stops merges on a reviewer's opinion, not on a measurement. Dismissals let a maintainer overrule a finding they disagree with.

## Commands and dismissals

Maintainers (authors whose association is in `command-authors`) can steer the review from the pull request:

- **`/algo-intelligence`** as a comment reviews the pull request now, including a draft, one without the `require-label` label, or code already reviewed.
- **`/algo-intelligence dismiss P3`** (one or more ids, from the comment's table) dismisses those findings: they move to a "Dismissed by maintainers" list in the comment, their review threads get a reply saying so (left open for you to resolve), later reviews are told not to report them, they no longer count in the outputs, and a review job that failed on them is re-run and passes if nothing else blocks. Replying **`/algo-intelligence dismiss`** on one of the action's review comments dismisses that comment's finding.

Dismissals are read from the pull request's comments at the start of every review, so they work with the workflow above, taking effect on the next push. To have commands act at once, add a second workflow for comments, for example as algorithmic-intelligence-command.yml in .github/workflows; it runs from your default branch with your secrets, like `pull_request_target`, so it follows the same rules (read the pull request's code, never run it):

```yaml
name: Algorithmic Intelligence - command

on:
  issue_comment:
    types: [created]
  pull_request_review_comment:
    types: [created]

permissions:
  contents: read
  pull-requests: write
  actions: write         # re-runs a review job that failed on a finding a maintainer dismissed

jobs:
  review:
    name: Algorithmic Intelligence - command
    if: startsWith(github.event.comment.body, '/algo-intelligence') && (github.event.issue.pull_request || github.event.pull_request)
    runs-on: ubuntu-latest
    timeout-minutes: 30
    concurrency:
      group: algorithmic-intelligence-${{ github.event.issue.number || github.event.pull_request.number }}
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1  # v7.0.1
        with:
          ref: refs/pull/${{ github.event.issue.number || github.event.pull_request.number }}/head   # to read, never to run
          fetch-depth: 0
          persist-credentials: false
      - uses: protechnocrats/algorithmic-intelligence@0.7.5
        with:
          anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}
```

A dismissal needs no model and is recorded without a review. A comment from anyone outside `command-authors`, or from a bot, is ignored. A fork's pull request is reviewed on command only when `allow-forks` is `true`; the trusted commenter stands in for `fork-authors` and `fork-label`. The pull request's author can dismiss findings on their own pull request when their association is in `command-authors`; narrow it (for example to `OWNER`) if that is not what you want.

## What it skips

- Pull requests that change only documentation, images, licenses, or lock files, or only files matching `exclude-paths`.
- Draft pull requests. The example workflows do not run on them at all (the job's `if:`), so a draft shows the check as skipped rather than as a green pass; marking the pull request ready for review reviews it. A maintainer can still review a draft on demand with `/algo-intelligence`. Without that `if:` the job runs, sees the draft, and stops without a review (`review-drafts: true` reviews drafts instead).
- Pull requests without the `require-label` label, when it is set.
- Pushes that leave the code unchanged since the last review: documentation edits, a clean rebase, or a re-run. The comment records a fingerprint of the pull request's code changes, the `instructions` and configuration file, and the action version, and a push with the same fingerprint is not reviewed again (the `status` output is `unchanged`, and the counts repeat the last review's). A quiet review, which posts no comment, keeps its fingerprint in the Actions cache instead, so a clean pull request is not paid for again either; where the cache is unavailable, its next push is reviewed again.
- Pull requests from forks, unless you set them up as described below. GitHub does not give workflows triggered by a fork's pull request (`pull_request`) the repository's secrets, so there are no model credentials; the run says so and passes.

A review that does not finish (Claude Code fails to start, an authentication or API error, the budget or time limit reached) says so in the comment, above the last report that finished if there is one, and fails the job, so a broken setup shows as a red check instead of hiding behind a green one; re-run the job once the cause is fixed. If you make the check required, an API outage then blocks merges until a re-run succeeds; set `fail-on-error: false` to let such a run pass, as it did before. Network errors while posting are warnings, not failures. The action also fails the job for a broken setup (the checks in "Pull requests from forks", an unknown `provider`), and on a finding at or above `block-on-severity` (see "Blocking merges").

## Pull requests from forks

Reviewing a fork's pull request needs the `pull_request_target` trigger, which runs the workflow from your base branch with your secrets and a write token. That trigger is dangerous when a workflow runs the pull request's code: a build, a test, an install script. This action runs none of it: the scripts it runs come from the action's own pinned release, and the agent can only read files. Even so, set it up exactly like this, in a workflow of its own, with no other steps:

```yaml
name: Algorithmic Intelligence

on:
  pull_request_target:
    types: [opened, synchronize, reopened, ready_for_review, labeled]

permissions:
  contents: read
  pull-requests: write

concurrency:
  group: algorithmic-intelligence-${{ github.event.pull_request.number }}
  cancel-in-progress: true

jobs:
  review:
    name: Algorithmic Intelligence - review
    if: github.event.pull_request.draft == false   # drafts are not reviewed; marking one ready reviews it
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1  # v7.0.1
        with:
          ref: ${{ github.event.pull_request.head.sha }}   # the pull request's code, to read, never to run
          fetch-depth: 0
          persist-credentials: false
      - uses: protechnocrats/algorithmic-intelligence@0.7.5
        with:
          anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}
          allow-forks: true
          fork-label: algorithmic-intelligence
```

This one workflow reviews pull requests from branches in your repository too, so it replaces the `pull_request` workflow rather than joining it.

- **Who gets reviewed.** A fork's pull request is reviewed only when its author's association is in `fork-authors` (by default owners, organization members, and collaborators), or when a maintainer adds `fork-label`. Anyone else's pull request is skipped, so strangers cannot spend your API budget; adding the label after reading the pull request is the way to review one.
- **Never add a step that runs the checked-out code** (a build, tests, `npm install`, a cache restore keyed on its files) to this workflow. That is what makes `pull_request_target` dangerous, and nothing in this action can protect you from it.
- **The action checks the setup.** It stops if the checkout is not the pull request's code, or if the checkout kept the GitHub token in `.git/config`.

## Other model providers

Set `provider` to run the model on Amazon Bedrock or Google Vertex AI, with credentials set up earlier in the job. Both are best done with OpenID Connect, so no long-lived key is stored; the job then needs `id-token: write`.

Amazon Bedrock:

```yaml
permissions:
  contents: read
  pull-requests: write
  id-token: write
...
      - uses: aws-actions/configure-aws-credentials@<pinned SHA>
        with:
          role-to-assume: arn:aws:iam::123456789012:role/algorithmic-intelligence
          aws-region: us-east-1
      - uses: protechnocrats/algorithmic-intelligence@0.7.5
        with:
          provider: bedrock
          # model: a Bedrock model ID or inference profile, if the default is not enabled in your account
```

Google Vertex AI:

```yaml
      - uses: google-github-actions/auth@<pinned SHA>
        with:
          workload_identity_provider: projects/123/locations/global/workloadIdentityPools/github/providers/repo
          service_account: algorithmic-intelligence@my-project.iam.gserviceaccount.com
      - uses: protechnocrats/algorithmic-intelligence@0.7.5
        with:
          provider: vertex
          vertex-project-id: my-project
          vertex-region: us-east5
```

The review step passes the provider's settings to Claude Code and leaves out the Anthropic credentials. `google-github-actions/auth` writes its credentials file into the checkout, where the agent could read it, so the action moves any credentials file that `GOOGLE_APPLICATION_CREDENTIALS` and the similar AWS and Google variables point at out of the checkout while the agent runs, and puts it back afterwards. The cost shown in the comment is Claude Code's estimate at Anthropic's prices; your cloud bill is the authority. Unlike the model credentials of the default provider, cloud credentials set up by an earlier step are in the environment of every later step, including those that hold the GitHub token; the agent itself still has no shell and no network.

## Code scanning (SARIF)

With `sarif: true`, the action also writes the findings as SARIF and gives the path in the `sarif-file` output, for upload to code scanning, where findings get GitHub's own alert list and dismissal workflow. Code scanning on private repositories needs GitHub Advanced Security, and the upload needs `security-events: write`:

```yaml
      - uses: protechnocrats/algorithmic-intelligence@0.7.5
        id: review
        with:
          anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}
          sarif: true
      - if: steps.review.outputs.sarif-file != ''
        uses: github/codeql-action/upload-sarif@<pinned SHA>
        with:
          sarif_file: ${{ steps.review.outputs.sarif-file }}
          category: algorithmic-intelligence
```

## Security model

The pull request under review is untrusted: its code, comments, and documentation can contain instructions aimed at the agent. The action limits what such instructions can achieve.

- **The agent can only read.** Claude Code runs with `--restricted` and only the Read, Grep, Glob, and Skill tools: no shell, no file edits, no web access, and no MCP servers. Restricted mode also confines reading to the checkout and the action's work directory, and ignores the repository's Claude Code settings and hooks. The agent cannot run the project's code, its tests, or its build scripts.
- **Credentials are split across steps.** The step that runs the agent has the model credentials and no GitHub token. The steps that prepare the review (reading the previous comment, and recording a dismissal) and post it have the GitHub token and no model credentials. With `persist-credentials: false`, the token is not in `.git/config` either, and the action refuses to run if it is. A cloud credentials file inside the checkout is moved out of the agent's reach while it runs (see "Other model providers").
- **Maintainer settings come from outside the pull request.** `instructions` come from the workflow, and the configuration file is read from the base commit, so a pull request cannot rewrite what the reviewer is told about sizes. Commands and dismissals are obeyed only from `command-authors`.
- **The install is integrity-checked.** Claude Code is installed with `npm ci` from a lockfile in the action holding the integrity hash of every package, with install scripts disabled except Claude Code's own, which puts the native binary for the runner's platform in place; a tampered package on the registry fails the install instead of running.
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
- The skill's main evaluation measured interactive sessions that could run code. This read-only review was evaluated separately, on a small set of pull requests (see "Pull request review" in [RESULTS.md](RESULTS.md)).
- Severity is the reviewer's judgment from the stated sizes, and line numbers are its reading of the file; a finding whose line is not in the diff stays in the comment only.
