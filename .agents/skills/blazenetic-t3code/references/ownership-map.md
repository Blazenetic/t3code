# Downstream ownership and risk map

Use this map after reading the current `../blazenetic/CUSTOMISATION-GUIDE.md`;
that guide remains authoritative when the two differ.

| Area                                                                                  | Ownership                     | Typical risk |
| ------------------------------------------------------------------------------------- | ----------------------------- | ------------ |
| `.agents/skills/blazenetic-t3code/`, `scripts/blazenetic/`, `.env.blazenetic.example` | Downstream                    | Low          |
| `../blazenetic/` operating guides                                                     | Local downstream, outside Git | Low          |
| `apps/web/src/blazenetic/`, `apps/web/src/components/blazenetic/`                     | Downstream modules            | Medium       |
| `apps/server/src/blazenetic/`                                                         | Downstream modules            | Medium       |
| Settings navigation and provider registry contribution mounts                         | Upstream-owned thin mounts    | Medium       |
| `ChatView`, right-panel state, sidebar composition                                    | Upstream core                 | High         |
| Contracts, RPC/event model, orchestration, workspace/package layout                   | Upstream core                 | Very high    |
| Generated files and `.repos/`                                                         | Never hand-edit               | Prohibited   |

Before changing a Medium-or-higher area, explain why a Low-risk external or
additive solution is insufficient. Keep any unavoidable upstream mount minimal
and update `../blazenetic/ARCHITECTURE-NOTES.md`.
