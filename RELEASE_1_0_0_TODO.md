# 1.0.0 Release TODO

Porytiles main repo shipped `v1.0.0` on 2026-06-05.
This docs repo (and `porytiles-dev-docs`) follow with their own release-branch flow,
tracked as [grunt-lucas/porytiles#313](https://github.com/grunt-lucas/porytiles/issues/313).

The canonical runbook lives in the main repo at `RELEASE_PROCESS.md`,
section "Regular versioned release" → step 8 (Docs repos lockstep).
This file is the per-repo wrap-up checklist for closing the docs side of the 1.0.0 cut.
Delete this file once the last box is ticked.

## Pre-flight

- [ ] Finish the in-flight content on `develop` (the WIP `docsrc/quickstart.md`,
      `docsrc/index.rst` edits, anything else slated for the 1.0.0 cut).
- [ ] Local Sphinx build is clean: `cd docsrc && uv run make html`.
- [ ] Page titles render "Porytiles ... 1.0.0 documentation".
- [ ] `VERSION` file already reads `1.0.0` (from Phase F2); the runbook's
      "bump VERSION on release branch" step is a no-op for this cut.
      Future releases will exercise it.

## Cut and ship — run in both `porytiles-user-docs` and `porytiles-dev-docs`

Follow `RELEASE_PROCESS.md` step 8 exactly.
The PR `release/1.0.0` → `master` is what creates `master` at merge
and serves as the archival diff documenting the full 1.0.0 docs state.

- [ ] `porytiles-user-docs`: cut, PR, merge, tag `v1.0.0`, merge back to develop, delete release branch.
- [ ] `porytiles-dev-docs`: same.

## Coordinated settings flip — per repo, after `master` exists

- [ ] GH Pages source from `develop /docs` to `master /docs`:
  ```sh
  gh api -X PUT repos/grunt-lucas/porytiles-user-docs/pages \
    -f source.branch=master -f source.path=/docs
  gh api -X PUT repos/grunt-lucas/porytiles-dev-docs/pages \
    -f source.branch=master -f source.path=/docs
  ```
- [ ] In each repo's `docsrc/conf.py`, change `github_version` from `'develop'` to `'master'`
      so the "Edit on GitHub" links target the served branch.
      Commit this as a small follow-up PR on `develop`,
      then carry it into the next release-branch cut.

## Lock down — per repo, after `master` exists

- [ ] **F6 — Branch + tag protection.** Mirror the main `porytiles` repo's pattern:
  - `master`: PR required, no force-push, no deletion.
  - `develop`: same.
  - Repository Ruleset on `refs/tags/v*` blocking `deletion`, `update`, `non_fast_forward`.
- [ ] **F8 — End-to-end verify** each docs repo:
  - `git checkout v1.0.0` builds cleanly via Sphinx.
  - Push to `master` triggers GH Pages deploy and the public site updates.
  - The `|release|` substitution renders `1.0.0` everywhere it appears.

## Close out

- [ ] Close [grunt-lucas/porytiles#313](https://github.com/grunt-lucas/porytiles/issues/313)
      with a short comment linking the docs `v1.0.0` releases.
- [ ] Delete this file.
