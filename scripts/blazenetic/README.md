# Blazenetic fork tools

This is the portable entry point for the downstream tooling. Read the repository
[AGENTS.md](../../AGENTS.md) and [fork skill](../../.agents/skills/blazenetic-t3code/SKILL.md).
Product development follows upstream's architecture and validation rules.

## Start an agent task

```sh
git status --short --branch
git worktree list
scripts/blazenetic/t3b-agent status
```

On the configured CachyOS host, also run `t3b-maintain status`. The complete local
manual is beside the main checkout at `../blazenetic/README.md`; current project
authority and the single current handover are in
`../projects/blazeprovements/README.md`. For linked worktrees, locate the main
checkout with `git worktree list --porcelain` and resolve those sibling paths
from there. These relative paths describe the host layout, not GitHub links.

A fresh clone or cloud agent may have neither that manual nor installed `t3b*`
commands. Use this README, the fork skill and the current user's task as the
starting context. Report missing local records rather than inventing their
contents or treating a historical task as new authority. Do not install host
services or assume the clone contains the user's runtime or credentials.

## Daily use and development

Official nightly is an installed daily app, separate from this source checkout.
Its desktop client and NetBird server have separate installations and may need
separate updates. Use the app's update action; an explicit `t3b-netbird update`
updates/restarts the host. Finish active work before a deliberate restart.
Fork synchronization never updates that runtime or adds private features to it.

For development, use a feature branch/worktree based on local `blazenetic`,
install dependencies with `vp i --frozen-lockfile`, then run
`scripts/blazenetic/t3b-web` or `scripts/blazenetic/t3b-desktop`. These wrappers
use checkout-local `.t3` state and select the current linked worktree. Native
`vp run dev` remains available on a fresh clone. Never point development at daily
data. A custom daily binary needs its own future build and update arrangement.

## Branch contract

| Ref                                                              | Purpose                                                  |
| ---------------------------------------------------------------- | -------------------------------------------------------- |
| `upstream/main`                                                  | Canonical T3 source; upstream push URL must be `no_push` |
| `main`, `origin/main`                                            | Clean mirrors; no downstream commits                     |
| Local `blazenetic`                                               | Accepted downstream baseline on the configured host      |
| `origin/chore/fork-maintenance`                                  | Published maintained baseline                            |
| `feature/*`, `fix/*`, `chore/*`                                  | Scoped development based on that baseline                |
| Historical `origin/blazenetic`, `origin/feature/blazeprovements` | Preserved old setup; not current baselines               |

The fork remote is `https://github.com/Blazenetic/t3code`; upstream is
`https://github.com/pingdotgg/t3code.git`. Accepted upstream integration uses
merges to preserve customization commit identities. Feature work is not adopted
into the baseline automatically. Validate and accept the feature under its own
task before integrating it. Upstream contributions start from current main and
follow [CONTRIBUTING.md](../../CONTRIBUTING.md); no upstream contact is implied.

## Maintenance commands on the configured host

| Command                                   | Effect                                                                                                      |
| ----------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| `t3b-maintain status`                     | Read local state and timer enablement; no online freshness check                                            |
| `t3b-maintain prepare`                    | Fetch main refs, merge upstream into a separate candidate and check it; no push or adoption                 |
| `t3b-maintain update`                     | Prepare/check, adopt local baseline with backup, then normally push the maintained branch                   |
| `t3b-maintain publish`                    | Push the existing local baseline without running checks; intended for an already-reviewed publication retry |
| `t3b-maintain run`                        | Timer operation: fast-forward the hosted mirror and unoccupied local main, then prepare/check only          |
| `scripts/blazenetic/t3b-maintain install` | Copy reviewed source tools and enable/update the daily user timer                                           |
| `t3b-sync status` / `fetch`               | Low-level cached-ref inspection / explicit ref refresh                                                      |
| `scripts/blazenetic/t3b-agent check`      | Focused downstream tests and syntax/whitespace checks                                                       |

The timer runs around 09:20–09:40 local time and catches up after downtime. It
needs an awake host, network access and local GitHub credentials. It never adopts
a customization update, switches a feature branch or restarts nightly. `update`
leaves the active feature branch unchanged; merge accepted `blazenetic` into it
explicitly when ready. Never discard unfinished work to make an update proceed.

Prepared updates pass downstream tooling tests, locked dependency installation
and isolated web/environment HTTP startup. This does not establish complete
product, provider, mobile or GUI acceptance. Unchanged ready candidates reuse
their checks. Legacy rebase-based `t3b-sync apply` is retired.

## Recovery and installed copies

```sh
systemctl --user status t3b-maintain.service
systemctl --user list-timers t3b-maintain.timer
systemctl --user disable --now t3b-maintain.timer  # pause future checks
systemctl --user enable --now t3b-maintain.timer  # resume
```

Maintenance state and private check output live under
`~/.local/share/t3code-maintenance/`. The detached `candidate/` worktree is managed
by the updater; edits, conflicts or unexpected commits stop preparation. Inspect
and preserve that work before recovery. Do not clean/remove the worktree or edit
its status records blindly. `maintenance/ready` retains a checked commit, and
baseline adoption creates `backup/*` refs. A rejected push preserves the local
baseline; inspect the remote difference before retrying publication.

The installed command/helper live under `~/.local/lib/t3code-blazenetic/`.
`t3b-maintain` invokes that copied version, so branch switches do not remove it.
After reviewing tool code changes, refresh it by invoking the source path
`scripts/blazenetic/t3b-maintain install`; invoking the installed copy's `install`
does not copy newer source code. Documentation-only changes need no reinstall.

Runtime updates and recovery remain deliberate operator actions. Never publish
pairing credentials or raw private logs. No routine command force-pushes,
rewrites historical branches, writes upstream, creates a PR or publishes a release.
