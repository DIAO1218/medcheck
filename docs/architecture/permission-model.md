# Permission Model

**Default: no read, no write.** Every path below is an explicit whitelist entry. Anything not listed is denied, and denial is logged (`permission.denied.count`, blueprint §9). The machine-readable form is `.opencode/permissions.jsonc`; `test/offline/test_permissions.py` asserts that the two stay in sync and that unlisted paths are denied.

Three roles, because the pipeline has three trust positions: one that may only look (`plan-agent`), one that may build but not govern (`build-agent`), one that may only judge (`verify-agent`). Human-only surfaces exist because an agent that can edit its own rules can edit away its constraints.

---

## 1. Role matrix

| Path | `plan-agent` | `build-agent` | `verify-agent` | human-only |
|---|---|---|---|---|
| `AGENTS.md` | read | read | read | **write** |
| `architecture-blueprint.md` | read | read | read | **write** |
| `Prompt.md` | read | read | read | **write** |
| `Report.md` | **write** | read | read | write |
| `docs/req/**` | **write** | read | read | write |
| `docs/architecture/**` | read | read | read | **write** |
| `docs/code-governance/**` | read | read | read | **write** |
| `docs/ai-use-log.yaml` | read | **write (append only)** | read | write |
| `docs/review-memo.md` | read | read | **write** | write |
| `docs/debt-register.md` | read | **append** | **append** | write |
| `docs/bug-diary.md` | read | **append** | **append** | write |
| `prompts/**` | read | **write** | read | write |
| `src/**` | read | **write** | read | write |
| `test/**` | read | **write** | read | write |
| `data/rules/**` | read | **read only** | read | **write** |
| `data/audit/**`, `data/state/**`, `data/cache/**` | **denied** | **denied** | **denied** | n/a (runtime only) |
| `.opencode/**` | denied | **denied** | denied | **write** |
| `.agent/**` | denied | **denied** | denied | **write** |
| `.github/workflows/**` | denied | **denied** | denied | **write** |
| `scripts/**` | read | **write** | read | write |
| `transcripts/**` | **append** | **append** | read | write |
| `.workbuddy/memory/**` | **write** | **write** | read | write |
| everything else | denied | denied | denied | — |

Notation: *read* = read-only; *write* = read + write; *append* = create new records, cannot modify or delete existing ones; **denied** = neither read nor write, and the attempt is logged.

## 2. Why these three denials exist

| Denial | Threat it closes |
|---|---|
| `build-agent` cannot write `.opencode/`, `.agent/`, `AGENTS.md`, `architecture-blueprint.md` | The agent that writes code must not write the constraints its code is judged against. Otherwise INV-003 is one PR away from being deleted by the same actor it constrains. |
| No agent may write `docs/architecture/**` | ADRs are the record of human judgement. An agent-authored ADR would let the build rationalise its own deviations. Agents *propose* in a PR comment; humans commit. |
| Every agent is denied `data/audit/**` and `data/cache/**` | Those stores contain case-derived data. Read access alone would let an agent paste pseudonymous case content into a prompt or a transcript (INV-004). |

## 3. Guard rules (enforced, not documented)

| Guard | Mechanism | Failure mode |
|---|---|---|
| Path whitelist | `.opencode/permissions.jsonc` evaluated before any tool call | tool call returns `PermissionDenied`, logged |
| Safety-critical write | writes under `src/medcheck/{adjudicator,rules,privacy,audit}` require an ADR id in the PR body and a human approval | CI gate 6 fails the PR (REQ-G-004) |
| Table mutation | `build-agent` has read-only on `data/rules/**`; table changes go through a human PR with schema gate | write attempt denied; PR blocked |
| Append-only stores | `audit` and `debt-register` opened in append mode; `audit` additionally hash-chained | tamper raises `AuditImmutableError` (REQ-F-007) |
| Secret paths | `.env`, `*.pem`, `secrets/**` denied to all roles | denial logged, secret scan gate also checks |
| Shell execution | `build-agent` may run `python -m pytest`, `python scripts/*.py`, `git diff/status/log` only; arbitrary shell is denied | command allowlist in `permissions.jsonc` |
| Network | only the model endpoint, and only from `extractor.llm` | egress allowlist, tested in `test/offline/test_permissions.py::test_egress_allowlist` |

## 4. Enforcement points

1. **Agent runtime** — `.opencode/permissions.jsonc` is read by the coding agent at session start; violations are refused before the tool executes.
2. **CI** — `scripts/check_permissions_sync.py` fails if a path in the blueprint's matrix is missing from `permissions.jsonc`, or if a role is granted a permission the matrix denies.
3. **Tests** — `test/offline/test_permissions.py` requests 12 non-whitelisted paths across the 3 roles and asserts 12 denials (REQ-G-002's fit criterion).
4. **Review** — the review memo has a mandatory "permission surface changed?" line; an unexplained change is `CHANGES REQUIRED`.

## 5. Human-only surfaces (why an agent can never hold these)

`AGENTS.md` · `architecture-blueprint.md` · `Prompt.md` · `.opencode/**` · `.agent/**` · `.github/workflows/**` · `docs/architecture/**` · `docs/code-governance/**`

These nine surfaces define the rules, the gates, and the judgement record. If an agent could write them, every invariant would be advisory — a constraint the constrained party can edit is not a constraint. This is the single most important line in this document, and it is why `.agent/rules.md` is marked *human-only* in the project covenant.
