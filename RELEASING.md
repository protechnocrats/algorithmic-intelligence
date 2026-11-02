# Releasing

Every release has a version tag and published release notes. The notes come from `CHANGELOG.md`; the release workflow refuses to publish a version that has no notes.

## Versions

Versions follow [semantic versioning](https://semver.org), and tags are written `v<major>.<minor>.<patch>` (for example `v0.1.0`).

- **Patch** (`v0.1.1`): wording fixes, corrected facts or citations, eval and tooling fixes. No intended change in how agents behave.
- **Minor** (`v0.2.0`): new or changed instructions, rules, modes, techniques, or language files, anything that can change what an agent does. While the major version is 0, a minor release may also change behavior incompatibly.
- **Major** (`v1.0.0`): the first stable release, and later any incompatible change after it.

## Between releases

Every pull request that changes the skill adds a line to the `[Unreleased]` section of `CHANGELOG.md`, describing the change for someone who installs the skill: what the agent now does differently, not which file changed. The pull request checks fail if the `[Unreleased]` heading is missing. If a change is measured (an eval round), link its results file.

## Making a release

1. **Prepare it in a pull request.** In `CHANGELOG.md`, rename `[Unreleased]` to the new version with today's date (`## [0.2.0] - YYYY-MM-DD`), add a short summary at the top of the section, and start a new empty `## [Unreleased]` section above it. Run `evals/token-budget.sh`. Merge the pull request once its checks pass.
2. **Tag the merge commit on `main`:**

   ```bash
   git switch main && git pull
   git tag -a v0.2.0 -m "v0.2.0"
   git push origin v0.2.0
   ```

3. **The release publishes itself.** Pushing the tag runs `.github/workflows/release.yml`, which takes the tag's section from `CHANGELOG.md` and publishes a GitHub release with it as the notes. Check the release page afterward.

Tags matching `v*` are protected: they cannot be moved or deleted (see `.github/rulesets/`), so a published version always means the same files. If a release is wrong, publish a new patch release instead of moving the tag.

## Repository rules

`.github/rulesets/` holds the repository's rulesets as JSON, so they are reviewed like code. To apply or update one: on GitHub, **Settings → Rules → Rulesets → New ruleset → Import a ruleset**, and choose the file.

- `main-branch.json`: changes reach `main` only through pull requests whose checks pass (`skill-checks`); review threads must be resolved; no force pushes, no deletion, linear history (squash or rebase merges). Repository administrators can bypass the rules only through a pull request (bypass mode `pull_request`): even an administrator cannot push to `main` directly, but can merge a pull request without waiting for its checks in an emergency. Once there is a second maintainer, raise the required approvals from 0 to 1.
- `release-tags.json`: tags matching `v*` cannot be deleted or moved; administrators can bypass.
