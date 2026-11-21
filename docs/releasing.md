# Releasing

## Versions

- Releases are git tags `vMAJOR.MINOR.PATCH` ([Semantic Versioning](https://semver.org/)). The tag, `version` in
  `pyproject.toml` and the newest release section in `CHANGELOG.md` always agree. `tests/test_release.py` and
  `lc release-check` enforce this.
- **0.0.z is the beta series.** Every release bumps PATCH only (0.0.1, 0.0.2, …), whether it adds features or fixes
  bugs. Leaving the beta (0.1.0 or 1.0.0) is an explicit decision by the maintainer, not a routine bump. GitHub marks
  0.0.z releases as pre-releases.
- `version` in a model's `model.yaml` is the version of that build. It is independent of the repository version.

## While developing

Every change that someone using the tool or the manuals would notice adds a line under `## [Unreleased]` in
`CHANGELOG.md` (grouped as Added, Changed, Fixed or Removed), in the same commit as the change.

## Cutting a release

1. Branch `release/vX.Y.Z` from `main`.
2. In `CHANGELOG.md`, move the entries under `[Unreleased]` into a new section `## [X.Y.Z] - YYYY-MM-DD` and leave an
   empty `## [Unreleased]` at the top. Update the compare links at the bottom.
3. Set `version = "X.Y.Z"` in `pyproject.toml`, then run `uv lock`.
4. Run `uv run pytest` and `uv run lc release-check vX.Y.Z`. The second prints the release notes.
5. Commit as `chore(release): vX.Y.Z` and merge into `main`.
6. On `main`, run `git tag -a vX.Y.Z -m "vX.Y.Z"`, then push `main` and the tag. The Release workflow publishes the
   GitHub release from the changelog section, and the Pages workflow redeploys the site from `main`.
