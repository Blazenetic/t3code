---
name: blazenetic-t3code
description: Orient, plan, implement, validate, review, synchronize, or hand off work in the Blazenetic downstream fork of T3 Code. Use whenever a request names Blazenetic, T3 Code, t3code, blazeprovements, the t3b wrappers, fork maintenance, downstream customization, upstream sync, or any task in the Blazenetic T3 Code checkout.
---

# Blazenetic T3 Code

Operate the fork through its repository-owned instructions and downstream
tooling. Preserve its clean-upstream model and make work recoverable by the next
human or agent.

## Orient before acting

1. Resolve the repository root and read the workspace `AGENTS.md`, repository
   `AGENTS.md`, and `../blazenetic/README.md`.
2. Run `t3b-agent status` from the repository root. If the wrapper is not
   installed, run `scripts/blazenetic/t3b-agent status`.
3. Treat dirty paths and concurrent worktrees as user-owned. Do not clean,
   stash, reset, switch, rebase, merge, or absorb them.
4. Read the topic guide routed by `../blazenetic/README.md`. For product edits,
   also read `references/ownership-map.md`.
5. State the active branch, tree state, authority, proposed paths, ownership
   class, conflict risk, acceptance gate, and hard stops before material edits.

Use the current user request as implementation authority only when it clearly
requests changes. Reviews, diagnoses, readiness checks, and plans remain
read-only.

## Choose the lowest-conflict change

- Prefer downstream-owned additions in `scripts/blazenetic/`, `.agents/skills/`,
  `.env.blazenetic.example`, isolated `apps/*/src/blazenetic/` modules, and the
  external `../blazenetic/` operating manual.
- Use existing settings and provider contribution seams before adding a new
  mount.
- Keep upstream-owned mounts thin and real behavior in downstream modules.
- Never edit generated output or `.repos/`.
- Avoid `ChatView`, contracts, orchestration, desktop lifecycle, workspace
  layout, and root package metadata unless the task explicitly justifies the
  rebase cost.
- Record a necessary Medium-or-higher downstream departure in
  `../blazenetic/ARCHITECTURE-NOTES.md`.

## Implement in reviewable units

Read before editing and use bounded searches. Preserve unrelated changes. Use
Vite+ (`vp` / `vp run`) as the project task interface; use Bun only for the
documented vendored-repository sync. Do not install dependencies, package,
publish, push, or contact upstream without explicit authority.

For UI work, follow the repository's `test-t3-app` or `test-t3-mobile` skill as
required by `AGENTS.md`. Never expose pairing tokens.

## Validate proportionally

Run focused tests for changed behavior first. For downstream agent/tooling
changes, run:

```bash
scripts/blazenetic/t3b-agent check
```

For product code, run targeted tests, formatting, lint, and type checks for the
affected packages. Follow repository `AGENTS.md`: full workspace checks are CI
work unless the user explicitly requests them. Run `git diff --check` and
inspect the final diff before handoff.

Do not claim a gate that did not run. Separate failures caused by the change
from pre-existing or environmental failures.

## Handle Git and upstream safely

- Keep `main` a fast-forward-only mirror of `upstream/main`.
- Put downstream changes on `blazenetic` or a feature branch based on it.
- Use `t3b-upstream` for a fetched read-only topology snapshot.
- Use `t3b-feature sync` for the long-lived feature workflow and `t3b-sync` for
  baseline-only integration.
- Never push to `upstream`. Sync never authorizes publish, and a local commit
  never authorizes push or PR creation.
- Do not improvise sync or recovery commands; follow
  `../blazenetic/UPSTREAM-SYNC.md`.

## Hand off durably

Run `scripts/blazenetic/t3b-agent handoff` and complete the emitted structure.
Lead with the outcome, then report material paths, ownership/risk, exact checks
and results, unrun checks, branch and working-tree state, and the one remaining
gate. Label the Git state exactly as `committed and clean`, `intentionally
uncommitted with handover`, or `blocked with files preserved`.
