# MCP Tool Manifest

The tools the coding agent may call, and which role may call them. A tool that is
not in this table is not callable, regardless of what the runtime offers — the
permission model's default is *no*, and this manifest is the whitelist.

Roles: `plan-agent`, `build-agent`, `verify-agent` (see `docs/architecture/permission-model.md`).

---

## 1. Filesystem

| Tool | plan | build | verify | Constraints |
|---|---|---|---|---|
| `read_file` | ✅ | ✅ | ✅ | denied for `data/audit`, `data/state`, `data/cache`, `data/telemetry`, `.env*`, `secrets/**` |
| `write_file` | ⚠️ restricted | ⚠️ restricted | ⚠️ restricted | per-role path lists in `.opencode/permissions.jsonc`; human-only surfaces always denied |
| `append_file` | ✅ (transcripts, memory) | ✅ (debt, bug diary, ai-use log) | ✅ (review memo, debt, bug diary) | append-only stores never truncated |
| `delete_file` | ❌ | ❌ | ❌ | deletion is a human action; agents propose it in the PR |
| `list_dir`, `glob`, `grep` | ✅ | ✅ | ✅ | inherit `read_file` denials |

## 2. Execution

| Tool | plan | build | verify | Constraints |
|---|---|---|---|---|
| `run_tests` | ❌ | ✅ | ✅ | `python -m pytest test/offline` only; `test/live` requires a human-set env |
| `run_script` | ❌ | ✅ | ✅ | only `scripts/*.py` that exist in the repo |
| `git_status`, `git_diff`, `git_log` | ✅ | ✅ | ✅ | read-only |
| `git_commit` | ❌ | ❌ | ❌ | commits are made by a human or by the CI bot on the human's instruction |
| `shell` (arbitrary) | ❌ | ❌ | ❌ | closed; the allowlist in `permissions.jsonc` covers the permitted cases |
| `network_fetch` | ❌ | ❌ | ❌ | the only egress is `extractor.llm`, at runtime, not at build time |

## 3. Model

| Tool | plan | build | verify | Constraints |
|---|---|---|---|---|
| `llm_extract` (the product's own path) | ❌ | ⚠️ live only | ❌ | never callable from an offline test; requires `MEDCHECK_LLM_*` and a human-set flag |
| agent's own reasoning | ✅ | ✅ | ✅ | not logged as a tool call; the transcript is the record |

## 4. Documents and review

| Tool | plan | build | verify | Constraints |
|---|---|---|---|---|
| `write_adr` (proposal) | ✅ as PR comment | ❌ | ❌ | never writes `docs/architecture/**`; humans commit ADRs |
| `write_review_memo` | ❌ | ❌ | ✅ | `docs/review-memo.md` only, append a new memo |
| `update_ai_use_log` | ❌ | ✅ | ❌ | append a new entry; existing entries immutable |

---

## 5. Why these specific prohibitions

| Prohibition | Failure it prevents |
|---|---|
| no `delete_file` for any role | An agent "cleaning up" a table row or a failing test, leaving a green build with less truth in it |
| no `git_commit` | Untraceable history; the commit is the human's assertion that they reviewed the diff |
| no arbitrary `shell` | The shell is the universal permission bypass — every path rule becomes advisory once a role can run `python -c` |
| no network at build time | Silent dependency adoption outside the allowlist (REQ-S-002) |
| `llm_extract` never in offline tests | A regression suite that needs a live model verifies the model's mood, not the code |
| ADR proposals as PR comments only | An agent that can write the record of human judgement can rationalise its own deviations (permission model §5) |

## 6. Manifest maintenance

- Adding a tool = a change to this file + a matching entry in `.opencode/permissions.jsonc` + a test in `test/offline/test_permissions.py`. All three, or the manifest is fiction.
- Removing a capability requires an ADR: a capability removed without a decision will be re-added by the next agent that finds it convenient.
- `scripts/check_permissions_sync.py` fails the build if a role's declared tools and the JSONC disagree on a human-only surface.
