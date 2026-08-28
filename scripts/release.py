#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = []
# ///
"""
Interactive driver for this docs repo's half of a Porytiles release.

Executes step 8 ("Docs repos lockstep") of the main repo's RELEASE_PROCESS.md
for the docs repo containing this script: cut release/X.Y.Z from develop, bump
VERSION, rebuild the served site, PR to master, tag, merge back to develop.
Steps that push to master, push tags, or delete branches pause for an explicit
"y". Run it only after the main compiler release for X.Y.Z is published and
verified.

An identical copy of this script lives in each docs repo (porytiles-user-docs
and porytiles-dev-docs); keep the two in sync. The main repo's
scripts/release.py step 8 invokes this script once per repo.

Usage:
    uv run scripts/release.py 2.1.0                # full docs cut of 2.1.0
    uv run scripts/release.py 2.1.0 --from tag     # resume at a given step
    uv run scripts/release.py 2.1.0 --dry-run      # print every command without executing
    uv run scripts/release.py --list-steps         # step names for --from
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

DRY_RUN = False
REPO_ROOT = None  # set in main()
REPO_NAME = None  # set in main()


def die(msg):
    print(f"\nrelease.py: FATAL: {msg}", file=sys.stderr)
    sys.exit(1)


def info(msg):
    print(f"\n==> {msg}")


def run(cmd, cwd=None, check=True):
    """Echo and execute a command. In dry-run mode, echo only."""
    where = f" (in {cwd})" if cwd else ""
    print(f"  $ {' '.join(cmd)}{where}")
    if DRY_RUN:
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
    result = subprocess.run(cmd, cwd=cwd, text=True)
    if check and result.returncode != 0:
        die(f"command failed with exit {result.returncode}: {' '.join(cmd)}")
    return result


def query(cmd, cwd=None):
    """Run a read-only command and return stripped stdout. Executes even in dry-run."""
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        die(f"query failed with exit {result.returncode}: {' '.join(cmd)}\n{result.stderr}")
    return result.stdout.strip()


def confirm(prompt):
    """A [confirm] gate from the runbook. Requires an explicit y. Aborts otherwise."""
    if DRY_RUN:
        print(f"  [confirm skipped in dry-run] {prompt}")
        return
    answer = input(f"\n[confirm] {prompt} [y/N] ").strip().lower()
    if answer != "y":
        die("aborted at confirmation gate. Re-run with --from <step> to resume.")


def pause(prompt):
    """An informational pause. ENTER continues."""
    if DRY_RUN:
        print(f"  [pause skipped in dry-run] {prompt}")
        return
    input(f"\n[review] {prompt} Press ENTER to continue. ")


def parse_semver(text):
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", text)
    if not match:
        die(f"'{text}' is not a plain X.Y.Z semver string")
    return tuple(int(part) for part in match.groups())


def step_preflight(version):
    """Verify a clean, current develop and that the main release for X.Y.Z shipped first."""
    info(f"{REPO_NAME} step 1: pre-flight")
    if query(["git", "status", "--porcelain"], cwd=REPO_ROOT):
        if DRY_RUN:
            print("  [dry-run] working tree is not clean; a real run stops here")
        else:
            die("working tree is not clean")
    run(["git", "checkout", "develop"], cwd=REPO_ROOT)
    run(["git", "pull"], cwd=REPO_ROOT)

    current = (REPO_ROOT / "VERSION").read_text().strip()
    if parse_semver(version) <= parse_semver(current):
        die(f"target version {version} is not greater than current VERSION {current}")

    # When this repo sits inside a main porytiles checkout (the layout RELEASE_PROCESS.md
    # assumes), the compiler release for X.Y.Z happens first and bumps that VERSION file.
    main_version_file = REPO_ROOT.parent / "VERSION"
    if (REPO_ROOT.parent / "RELEASE_PROCESS.md").exists() and main_version_file.exists():
        main_version = main_version_file.read_text().strip()
        if main_version != version:
            confirm(
                f"Main repo VERSION reads {main_version}, not {version}. The docs cut "
                "normally follows a published main release of the same version. Proceed?"
            )
    else:
        print("  (no main porytiles checkout at ../; skipping VERSION cross-check)")


def step_branch(version):
    """Cut release/X.Y.Z from develop and push it."""
    info(f"{REPO_NAME} step 2: create release/{version}")
    run(["git", "checkout", "develop"], cwd=REPO_ROOT)
    run(["git", "pull"], cwd=REPO_ROOT)
    run(["git", "checkout", "-b", f"release/{version}"], cwd=REPO_ROOT)
    run(["git", "push", "-u", "origin", f"release/{version}"], cwd=REPO_ROOT)


def step_build(version):
    """Bump VERSION, rebuild the served site, commit and push after review."""
    info(f"{REPO_NAME} step 3: bump VERSION and rebuild the site")
    run(["git", "checkout", f"release/{version}"], cwd=REPO_ROOT)
    if not DRY_RUN:
        (REPO_ROOT / "VERSION").write_text(f"{version}\n")
    # GitHub Pages serves the committed docs/ folder, and conf.py bakes VERSION into
    # the HTML at build time, so the site shows X.Y.Z only after this rebuild.
    run(["uv", "run", "make", "github"], cwd=REPO_ROOT / "docsrc")
    if not DRY_RUN:
        index = (REPO_ROOT / "docs" / "index.html").read_text()
        if version not in index:
            die(f"rebuilt docs/index.html does not mention {version}")

    run(["git", "add", "-A"], cwd=REPO_ROOT)
    run(["git", "--no-pager", "diff", "--stat", "--cached"], cwd=REPO_ROOT)
    pause("Review the staged changes (VERSION + rebuilt docs/), then")
    run(["git", "commit", "-m", f"Bump VERSION to {version} and rebuild site"], cwd=REPO_ROOT)
    run(["git", "push"], cwd=REPO_ROOT)


def step_pr(version):
    """Open and merge the release PR into master. Merging deploys the site."""
    info(f"{REPO_NAME} step 4: PR the release branch into master")
    run(["git", "checkout", f"release/{version}"], cwd=REPO_ROOT)
    run(["git", "fetch", "origin"], cwd=REPO_ROOT)

    clean = DRY_RUN or subprocess.run(
        ["git", "merge-tree", "--write-tree", "origin/master", f"release/{version}"],
        cwd=REPO_ROOT, capture_output=True,
    ).returncode == 0
    if not clean:
        # A docs hotfix on master that was never merged back to develop is the usual
        # cause. The docs repos sanction the master-into-develop merge for exactly this
        # (RELEASE_PROCESS.md, "Docs hotfix between releases").
        die(
            "the merge into master will conflict. Merge master into develop first\n"
            "(git checkout develop && git merge master), resolve, push, then re-run\n"
            f"from the top: uv run scripts/release.py {version}"
        )

    confirm(f"{REPO_NAME}: open the PR 'Release {version}' against master?")
    run([
        "gh", "pr", "create", "--base", "master", "--head", f"release/{version}",
        "--title", f"Release {version}", "--body", f"Docs cut of {version}.",
    ], cwd=REPO_ROOT)
    confirm(f"{REPO_NAME}: merge the PR? Merging deploys the site via GitHub Pages.")
    run(["gh", "pr", "merge", "--merge"], cwd=REPO_ROOT)


def step_tag(version):
    """Tag vX.Y.Z on master and push it."""
    info(f"{REPO_NAME} step 5: tag v{version} on master")
    run(["git", "checkout", "master"], cwd=REPO_ROOT)
    run(["git", "pull"], cwd=REPO_ROOT)
    on_master = query(["git", "show", "HEAD:VERSION"], cwd=REPO_ROOT)
    if not DRY_RUN and on_master != version:
        die(f"VERSION on master reads '{on_master}', expected '{version}'")
    confirm(f"{REPO_NAME}: push tag v{version}?")
    run(["git", "tag", "-a", f"v{version}", "-m", f"Porytiles docs {version}"], cwd=REPO_ROOT)
    run(["git", "push", "origin", f"v{version}"], cwd=REPO_ROOT)


def step_backmerge(version):
    """Merge the release branch back into develop and delete it."""
    info(f"{REPO_NAME} step 6: merge the release branch back into develop")
    run(["git", "checkout", "develop"], cwd=REPO_ROOT)
    run(["git", "pull"], cwd=REPO_ROOT)
    run(["git", "merge", "--no-ff", f"release/{version}"], cwd=REPO_ROOT)
    run(["git", "push"], cwd=REPO_ROOT)
    confirm(f"{REPO_NAME}: delete branch release/{version} (remote and local)?")
    run(["git", "push", "origin", "--delete", f"release/{version}"], cwd=REPO_ROOT)
    run(["git", "branch", "-d", f"release/{version}"], cwd=REPO_ROOT)
    info(f"{REPO_NAME} docs cut of {version} complete.")


STEPS = [
    ("preflight", step_preflight),
    ("branch", step_branch),
    ("build", step_build),
    ("pr", step_pr),
    ("tag", step_tag),
    ("backmerge", step_backmerge),
]


def main():
    global DRY_RUN, REPO_ROOT, REPO_NAME

    parser = argparse.ArgumentParser(description="Drive this docs repo's cut of a Porytiles release.")
    parser.add_argument("version", nargs="?", help="target version, e.g. 2.1.0")
    parser.add_argument("--from", dest="from_step", metavar="STEP",
                        help="resume from this step (see --list-steps)")
    parser.add_argument("--dry-run", action="store_true",
                        help="print every command without executing anything")
    parser.add_argument("--list-steps", action="store_true", help="list step names and exit")
    args = parser.parse_args()

    if args.list_steps:
        for name, func in STEPS:
            print(f"  {name:10s} {func.__doc__.splitlines()[0] if func.__doc__ else ''}")
        return

    if not args.version:
        parser.error("version is required (e.g. 2.1.0)")
    parse_semver(args.version)
    DRY_RUN = args.dry_run

    REPO_ROOT = Path(query(["git", "rev-parse", "--show-toplevel"]))
    REPO_NAME = REPO_ROOT.name
    if not (REPO_ROOT / "docsrc" / "conf.py").exists() or not (REPO_ROOT / "VERSION").exists():
        die(f"{REPO_ROOT} does not look like a Porytiles docs repo (no docsrc/conf.py + VERSION)")

    names = [name for name, _ in STEPS]
    start = 0
    if args.from_step:
        if args.from_step not in names:
            die(f"unknown step '{args.from_step}'; valid: {', '.join(names)}")
        start = names.index(args.from_step)

    for name, func in STEPS[start:]:
        func(args.version)


if __name__ == "__main__":
    main()
