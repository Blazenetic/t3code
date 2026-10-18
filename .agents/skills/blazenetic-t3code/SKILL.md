---
name: blazenetic-t3code
description: Develop and operate the Blazenetic T3 Code fork, its isolated development launchers, NetBird daily runtime, and guarded fork sync.
---

# Blazenetic T3 Code

Read repository AGENTS.md and the portable
[tooling README](../../../scripts/blazenetic/README.md). On the configured host,
also read workspace AGENTS.md, `../blazenetic/README.md` and
`../projects/blazeprovements/README.md`. In linked worktrees locate the main
checkout with `git worktree list --porcelain` and use its sibling manual/hub.
Fresh clones and cloud agents may lack those local records and installed tools;
report that limitation and use the current user's task as authority. Never infer
permission to install host services or access daily state from the README.
Run `scripts/blazenetic/t3b-agent status` from the chosen checkout.

Current-session implementation requests authorize their bounded local changes.
Reviews remain read-only. Report branch, dirty paths, authority, ownership,
write scope, and acceptance checks before editing. Preserve concurrent work;
parallel implementers use separate worktrees.

Keep downstream tooling in `scripts/blazenetic/`, agent guidance here, and
operating/project records outside the repository. Prefer native upstream
capabilities. No archived Settings or provider contribution seams exist in the
refreshed baseline. Do not port them without a concrete requirement.

`t3b`, `t3b-web`, and `t3b-desktop` are development commands, with explicit
checkout-local `.t3` state. The NetBird daily runtime is an installed release
outside Git; switching a development branch must not affect it. Never launch
against the user's live `~/.t3/userdata` or modify daily data for tests.

Run `scripts/blazenetic/t3b-agent check` for tooling changes, then focused
behavior tests. Product checks follow current repository AGENTS.md: targeted
tests/lint/types, no repo-wide checks unless requested. Do not launch browser
or computer-use validation without explicit user authority.

`t3b-maintain status` reports scheduled fork maintenance. `prepare` fetches main
and merges upstream into a detached candidate, then checks downstream tools,
locked dependencies and isolated HTTP startup. `update` prepares, fast-forwards
the unoccupied local blazenetic baseline with a backup, and publishes only to
origin/chore/fork-maintenance. It never switches the current feature branch.
Use `git merge blazenetic` explicitly to bring accepted updates into a feature;
inspect status first and preserve unfinished work. Do not edit the managed
candidate; use a dedicated feature worktree instead.

The installed daily t3b-maintain.timer runs a copied tool outside Git. Its `run`
command may only fast-forward origin/main and an unoccupied local main; it never
adopts a downstream candidate or restarts the daily app. Conflicts and failed
checks remain visible in t3b-maintain status. Refresh the installed tool with
`scripts/blazenetic/t3b-maintain install` from the reviewed checkout after
maintenance-tool changes; the normal t3b-maintain command runs an installed copy.
Documentation-only changes need no reinstall. `status` reads local records and
does not fetch; a ready record applies only to its recorded base/upstream commits.

`t3b-sync status` uses cached refs; `fetch` refreshes refs. Legacy rebasing via
`apply` is retired. Preserve historical origin/blazenetic and
origin/feature/blazeprovements; the maintained branch is
origin/chore/fork-maintenance. Routine main mirroring and publication to that
branch were authorized on 2026-10-18. Never force-push, push upstream,
change remotes, publish releases, or create a PR without separate authority.
This maintenance authority does not approve unrelated product features or their
integration. Start new work from an accepted task and verify its own scope/gate.

Use `t3b-agent handoff` and the session-closeout skill at closeout. Record exact
validation, limitations, final Git state, and remaining actions in the local
project hub. Never include pairing tokens or private service logs in records.
