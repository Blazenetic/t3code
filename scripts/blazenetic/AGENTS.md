# Blazenetic tooling instructions

Read the repository `AGENTS.md`, this directory's [README](README.md), and the
[fork skill](../../.agents/skills/blazenetic-t3code/SKILL.md) before changing
these tools. On the configured host, also read the workspace `AGENTS.md` and the
manual/project hub beside the main checkout. Those local records identify the
current accepted task and handover; this file does not authorize new work.

- Keep changes confined to the accepted task. Prefer these downstream paths to
  upstream product, package, release or workflow edits.
- Inspect branch, dirty paths and worktrees first. Preserve existing changes.
  Concurrent implementation needs a separate feature worktree. The managed
  maintenance candidate is reserved for the updater; never develop there.
- Official nightly and the NetBird host are installed outside Git. Development
  uses checkout-local `.t3`. Never use daily data, restart the host, change
  credentials or print pairing links as part of tooling tests.
- Run `scripts/blazenetic/t3b-agent check` for tooling or agent-guidance changes.
  Run focused behavior tests when code changes. Follow repository validation
  rules; do not run repo-wide checks or package builds routinely.
- The timer only mirrors `main` and prepares a checked candidate. Adoption and
  normal publication use explicit `t3b-maintain update`; inspect its effects in
  the README. Do not invoke it merely to check documentation.
- Preserve historical branches, backups and failed candidates. No reset, stash,
  forced push, upstream write, PR or release publication is implied by this file.
- Refresh installed tools from a reviewed source checkout only when needed:
  `scripts/blazenetic/t3b-maintain install`. Documentation edits alone need no
  reinstall or live-service operation.
- At closeout run `scripts/blazenetic/t3b-agent handoff`; record actual checks,
  branch/commit state, limitations and the next safe action in the local project
  hub when available. Keep personal state and handovers outside this repository.
