# Git for the Blazenetic Fork

How to use git in this clone. Rule of thumb: **push only to our fork; pull
upstream in with `t3b-sync`.** Never touch `pingdotgg/t3code` with a push or a
PR.

## Remotes

| Remote     | URL                                       | You may…           |
| ---------- | ----------------------------------------- | ------------------ |
| `origin`   | `https://github.com/Blazenetic/t3code`    | fetch **and** push |
| `upstream` | `https://github.com/pingdotgg/t3code.git` | **fetch only**     |

Check:

```bash
git -C ~/Code/t3code remote -v
# origin    …Blazenetic/t3code (fetch)
# origin    …Blazenetic/t3code (push)
# upstream  …pingdotgg/t3code.git (fetch)
# upstream  no_push (push)          ← must stay no_push
```

If upstream still has a real push URL, fix it (or re-run the installer):

```bash
git -C ~/Code/t3code remote set-url --push upstream no_push
~/Code/t3code/scripts/blazenetic/install-local-tools.sh
```

A local `pre-push` hook also refuses any push targeting `pingdotgg/t3code`.

## Branches

| Branch                          | Role                                                                                |
| ------------------------------- | ----------------------------------------------------------------------------------- |
| `main`                          | Clean mirror of `upstream/main`. **No** Blazenetic commits.                         |
| `blazenetic`                    | Long-lived downstream branch — all our customisations live here.                    |
| `feature/*`, `fix/*`, `chore/*` | Short-lived work branched off `blazenetic`.                                         |
| `backup/…`                      | Safety refs created by `t3b-sync` before a rebase. Keep until you confirm the sync. |

```bash
git switch blazenetic          # day-to-day work
git switch main                # only when syncing / inspecting the mirror
```

Do **not** commit customisations on `main`. If you do by mistake, see
[TROUBLESHOOTING.md](TROUBLESHOOTING.md).

## Day-to-day on `blazenetic`

```bash
cd ~/Code/t3code
git switch blazenetic
git pull --ff-only origin blazenetic   # if the branch already exists on the fork

# edit…
git status
git add <files>
git commit -m "feat(blazenetic): short why-focused message"

# publish to the FORK only
git push origin blazenetic
```

### Feature branches (optional, for non-trivial work)

```bash
git switch -c feature/my-change blazenetic
# …commit…
git switch blazenetic
git merge --no-ff feature/my-change
git push origin blazenetic
git branch -d feature/my-change
```

Prefer small, coherent commits — they rebase cleanly when upstream moves.

## First-time publish (fork is empty / behind)

When `blazenetic` and an updated `main` are ready on the machine but not yet on
GitHub:

```bash
git -C ~/Code/t3code push origin main
git -C ~/Code/t3code push -u origin blazenetic
# after a rebase (e.g. t3b-sync), history may need lease:
git -C ~/Code/t3code push --force-with-lease origin blazenetic
```

Never:

```bash
git push upstream …          # blocked; do not try
git push --force origin …    # prefer --force-with-lease when rewriting
```

## Syncing from upstream

Pull new upstream commits into our fork model with the wrapper (preferred):

```bash
t3b-sync                 # fetch, ff main, rebase blazenetic, validate
# review, then (printed by the script):
git push origin main
git push --force-with-lease origin blazenetic
```

Details and recovery: [UPSTREAM-SYNC.md](UPSTREAM-SYNC.md).

`t3b-sync` never pushes. Upstream is never a push target.

## Pull requests

Stay **inside the fork**. Do not open PRs against `pingdotgg/t3code`.

```bash
# create a PR on Blazenetic/t3code (base usually blazenetic)
gh pr create --repo Blazenetic/t3code --base blazenetic --head feature/my-change

# list PRs on the fork
gh pr list --repo Blazenetic/t3code
```

Use the downstream template when useful:
`.github/PULL_REQUEST_TEMPLATE/downstream-change.md`.

## Useful status commands

```bash
t3b-doctor                 # remotes, push guard, divergence summary
t3b-shell                  # cd into repo + branch/divergence banner

git status
git branch -vv
git log --oneline --graph --decorate -20

# how far is main from upstream?
git fetch upstream
git rev-list --left-right --count upstream/main...main

# how far is blazenetic from main?
git rev-list --left-right --count main...blazenetic
```

## Auth (HTTPS vs SSH)

`origin` is HTTPS by default. Pushing asks for your GitHub credentials (or a
credential helper / token). Optional SSH:

```bash
git remote set-url origin git@github.com:Blazenetic/t3code.git
# leave upstream as HTTPS fetch + no_push; or:
# git remote set-url upstream git@github.com:pingdotgg/t3code.git
# git remote set-url --push upstream no_push
```

## What not to do

| Don’t                                             | Do instead                                   |
| ------------------------------------------------- | -------------------------------------------- |
| `git push upstream …`                             | `git push origin …`                          |
| Open a PR against `pingdotgg/t3code`              | `--repo Blazenetic/t3code`                   |
| Commit Blazenetic work on `main`                  | Commit on `blazenetic` (or a feature branch) |
| Plain `git push --force`                          | `git push --force-with-lease`                |
| Merge upstream into `blazenetic` by hand casually | Prefer `t3b-sync`                            |
| Delete a `backup/…` ref before confirming sync    | Delete only after a good push + smoke check  |

## Related docs

- [UPSTREAM-SYNC.md](UPSTREAM-SYNC.md) — `t3b-sync` steps and recovery
- [DAILY-WORKFLOW.md](DAILY-WORKFLOW.md) — edit / check / package loop
- [SETUP-CACHYOS.md](SETUP-CACHYOS.md) — first-time remotes + install
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) — accidental `main` commits, upstream PR mistakes
