# Releasing

Every release has a version tag and published release notes. The notes come from `CHANGELOG.md`; the release workflow refuses to publish a version that has no notes.

## Versions

Versions follow [semantic versioning](https://semver.org), and tags are the bare version, `<major>.<minor>.<patch>` (for example `0.3.0`). Releases before 0.3.0 were tagged with a `v` prefix (`v0.1.0` to `v0.2.1`); those tags stay as they are.

- **Patch** (`0.3.1`): wording fixes, corrected facts or citations, and tooling fixes. No intended change in how agents behave.
- **Minor** (`0.4.0`): new or changed instructions, rules, modes, techniques, or language files, anything that can change what an agent does. While the major version is 0, a minor release may also change behavior incompatibly.
- **Major** (`1.0.0`): the first stable release, and later any incompatible change after it.

## Between releases

Every pull request that changes the skill adds a line to the `[Unreleased]` section of `CHANGELOG.md`, describing the change for someone who installs the skill: what the agent now does differently, not which file changed. The pull request checks fail if the `[Unreleased]` heading is missing. Do not put evaluation metrics, pass rates, or case names in the changelog or release notes (see "Evaluation" in [CONTRIBUTING.md](CONTRIBUTING.md)).

## Making a release

1. **Review what users will get.** Read the whole diff of `skills/` since the previous tag (`git diff <previous tag>..main -- skills/`), not only the changelog: every line is an instruction users' agents will follow. Check it as in "Reviewing changes to the skill" in [CONTRIBUTING.md](CONTRIBUTING.md), and that the changelog describes every change in behavior, above all any that touches approvals, commands, or untrusted content.
2. **Prepare it in a pull request.** In `CHANGELOG.md`, rename `[Unreleased]` to the new version with today's date (`## [0.3.0] - YYYY-MM-DD`), add a short summary at the top of the section, and start a new empty `## [Unreleased]` section above it. Set `version` in `plugin/.claude-plugin/plugin.json` to the new version and update the release tag in the README's install commands. Merge the pull request once its checks pass.
3. **Tag the merge commit on `main`:**

   ```bash
   git switch main && git pull
   git tag -a 0.3.0 -m "0.3.0"
   git push origin 0.3.0
   ```

4. **The release publishes itself.** Pushing the tag runs `.github/workflows/release.yml`, which takes the tag's section from `CHANGELOG.md` and publishes a GitHub release with it as the notes. Check the release page afterward.

Release tags (bare versions, and the older `v*` tags) are protected: they cannot be moved or deleted except by a repository administrator (see `.github/rulesets/`), so a published version means the same files unless an administrator moves the tag, which the maintainer never does. If a release is wrong, publish a new patch release instead of moving the tag.

## Repository rules

`.github/rulesets/` holds the repository's rulesets as JSON, so they are reviewed like code. To apply or update one: on GitHub, **Settings → Rules → Rulesets → New ruleset → Import a ruleset**, and choose the file.

- `main-branch.json`: changes reach `main` only through pull requests whose checks pass (`skill-checks`); review threads must be resolved; no force pushes, no deletion, linear history (squash or rebase merges). Repository administrators can bypass the rules only through a pull request (bypass mode `pull_request`): even an administrator cannot push to `main` directly, but can merge a pull request without waiting for its checks in an emergency. The required number of approvals is 0: the project has one maintainer, so review of every change (see "Reviewing changes to the skill" in [CONTRIBUTING.md](CONTRIBUTING.md)) is currently that maintainer's own review. Once there is a second maintainer, raise the required approvals from 0 to 1.
- `release-tags.json`: release tags (`[0-9]*` and the older `v*`) cannot be deleted or moved; administrators can bypass, so immutability of a published version rests on the maintainer not doing so.
