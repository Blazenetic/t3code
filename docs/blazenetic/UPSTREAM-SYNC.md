# Upstream Sync

Everyday git (remotes, branches, push targets): [GIT.md](GIT.md).

## Why `main` stays clean

`main` is a **pure mirror of `upstream/main`** and must never contain
Blazenetic-specific commits. Keeping it clean means we can always fast-forward
it to the latest upstream without conflicts, and rebase our `blazenetic` branch
on top. All customisations live on `blazenetic`.

## Push policy (non-negotiable)

| Remote     | Role                                  | Allowed ops      |
| ---------- | ------------------------------------- | ---------------- |
| `origin`   | Blazenetic fork (`Blazenetic/t3code`) | fetch + **push** |
| `upstream` | Canonical (`pingdotgg/t3code`)        | **fetch only**   |

Upstream's push URL is set to `no_push`, and a local `pre-push` hook refuses
any push whose target is `pingdotgg/t3code`. Do **not** open PRs against
upstream; keep all work inside the fork (`gh pr create --repo Blazenetic/t3code`
if needed).

## What `t3b-sync` does

Default mode is **rebase**:

1. Requires a clean working tree (refuses to run otherwise).
2. Verifies remotes: `origin` is the Blazenetic fork; `upstream` is fetch-only
   (disables upstream push if needed).
3. Fetches `origin` and `upstream` (never pushes).
4. Verifies local `main` has **no** commits absent from `upstream/main`. If it
   does, it stops and tells you to move them to `blazenetic` first.
5. Creates a backup ref: `backup/blazenetic-before-sync-YYYYMMDD-HHMMSS`.
6. Fast-forwards local `main` to `upstream/main` (`--ff-only`).
7. Rebases `blazenetic` onto `main`.
8. Runs `t3b-check` (unless `--no-check`).
9. Prints — **but never runs** — the **origin-only** push commands.

```bash
t3b-sync                 # rebase mode (default)
t3b-sync --merge         # merge mode (see below)
t3b-sync --no-check      # skip validation (discouraged)
```

### Safeguards

- Never deletes uncommitted work.
- Never uses plain `git push --force`.
- Never auto-pushes the rebased branch.
- Never pushes to `upstream` (fetch-only remote + pre-push guard).
- Always leaves a recoverable pre-sync ref.

## Rebase vs merge

- **Rebase (default):** keeps `blazenetic` a clean, linear set of downstream
  commits on top of upstream. History is rewritten, so publishing requires
  `--force-with-lease`. Best while `blazenetic` is effectively single-user.
- **Merge (`--merge`):** merges `main` into `blazenetic` instead of rebasing.
  Use this if `blazenetic` becomes a shared branch where rewriting history would
  disrupt collaborators. It creates merge commits and does not need a force push.

## After a successful sync

`t3b-sync` prints these; run them after reviewing:

```bash
# update the fork's clean mirror (fast-forward) — ORIGIN ONLY:
git -C ~/Code/t3code push origin main

# publish the rebased downstream branch (rewrites history — review first):
git -C ~/Code/t3code push --force-with-lease origin blazenetic

# NEVER:
# git push upstream ...
```

Then, once you've confirmed everything is good, delete the backup ref:

```bash
git -C ~/Code/t3code branch -D backup/blazenetic-before-sync-YYYYMMDD-HHMMSS
```

## Resolving conflicts

If the rebase (or merge) stops on a conflict, `t3b-sync` prints the recovery
steps. In summary:

```bash
git -C ~/Code/t3code status                 # see conflicted files
# edit files to resolve, then:
git -C ~/Code/t3code add <resolved-files>
git -C ~/Code/t3code rebase --continue      # (or: git commit, in --merge mode)
# or bail out entirely:
git -C ~/Code/t3code rebase --abort         # (or: git merge --abort)
```

Your pre-sync state is preserved on the `backup/...` branch either way.

## Recovering from a failed or unwanted sync

```bash
# restore blazenetic to exactly where it was before the sync:
git -C ~/Code/t3code switch blazenetic
git -C ~/Code/t3code reset --hard backup/blazenetic-before-sync-YYYYMMDD-HHMMSS
```

`main` only ever moves by fast-forward, so it is never in a lost state; if
needed, re-point it: `git branch -f main origin/main` (or `upstream/main`).

## Checking upstream divergence any time

```bash
t3b-doctor        # shows "main vs upstream/main" and "blazenetic vs main"
# or manually:
git -C ~/Code/t3code fetch upstream
git -C ~/Code/t3code rev-list --left-right --count upstream/main...main
```

## Manual fallback (no scripts)

If `t3b-sync` is unavailable, the equivalent by hand:

```bash
cd ~/Code/t3code
git status                              # must be clean
git fetch origin && git fetch upstream
git rev-list upstream/main..main        # must be EMPTY (no downstream commits on main)
git branch backup/blazenetic-manual-$(date +%Y%m%d-%H%M%S) blazenetic
git switch main && git merge --ff-only upstream/main
git switch blazenetic && git rebase main
# validate, then push with lease as above
```
