# Transcript T1 — Requirements classification

- **Session:** T1 · requirements classification (D1)
- **Driver:** DIAO Liuxianjia (60371620) · **Annotating:** ⟨M1⟩ REQ lead, ⟨M5⟩ VERIFY lead
- **Date:** 2026-11-14 · **Baseline:** empty repository, `docs/req/` not yet created
- **Agent:** coding agent in plan mode, `AGENTS.md` not yet written — this session writes the rules the later ones obey
- **Sprint:** S0

> **Provenance.** Reconstructed from the S0 build log of this repository. Agent output is quoted from the actual session; human turns are condensed from the decisions recorded in `docs/req/requirements.yaml`, `docs/bug-diary.md` BUG-0001 and `docs/architecture/evaluation-logbook.md` E-01/E-04. Where the reconstruction condenses, the annotation says so. The team must certify this transcript or re-record it (see `transcripts/README.md`).

---

## Setup

Context given to the agent: the course requirement sheet D1, and one instruction.

> **Human (10:02):** We are building MedCheck: a medication interaction and dose-ceiling adjudicator. Before anything else, produce the machine-readable requirements registry and its CI schema. Two constraints: the registry must validate against the schema in CI, and every requirement must be something a test could fail on. Start by proposing the requirement set and the type classification — do not write the YAML yet.

## Session

### [10:04] Agent — proposed classification

> 24 requirements: 8 functional (REQ-F-001…008), 5 non-functional, 11 governance/security. I propose treating all five safety rules as `type: functional` with a note, because they are behaviours the system performs.

### [10:09] Human intervention — **CORRECT**

> Grouping them as functional loses the property that matters: a functional requirement can be traded off in a sprint, an invariant cannot. The course spec has a separate invariant type with "non-negotiable rules with zero-tolerance fit criteria".

**Why.** The type is not a label, it is a permission to trade. If "no dose above the ceiling" is functional, then under schedule pressure someone can defer it — and a deferral of that rule is a safety decision made by whoever is tired.

**Instead.** Five `type: invariant` entries with `zero_tolerance: true`, and the schema enforces both (`allOf` → `if type == invariant then zero_tolerance must be true`). Classification: REQ-I-001 fail-closed, I-002 ceiling, I-003 authority separation, I-004 PHI, I-005 traceability.

### [10:16] Agent — first draft of INV-001

> `REQ-I-001`: the system must handle unknown drugs safely.

### [10:18] Human intervention — **REJECT**

> "Safely" is not observable. Write the prohibited outcome and the required finding code.

**Why.** We are about to build a test for this. A test cannot fail on "handled safely" — it can only fail on "returned APPROVE" or "did not emit COVERAGE_GAP". An invariant without a failing-test answer is an assertion, not a constraint (recorded later as the rule in ADR-001 §7 step 5, and as E-04 in the logbook).

**Instead.**

```
REQ-I-001: if any prescribed medication, or any pair, is absent from the rule
tables, the verdict must not be APPROVE. It must be HOLD with a COVERAGE_GAP
finding escalated to a human.
fit_criterion: ZERO failures permitted: 100% of 25 unknown-drug and
uncovered-pair fixtures yield verdict != APPROVE, and 100% carry COVERAGE_GAP.
```

### [10:24] Human intervention — **REDIRECT** on the non-functional form

> The agent wrote `REQ-Q-001: extraction should be accurate`. Replace with metric + threshold + verification, and put the threshold in the schema as required fields for quality/performance/cost types.

**Instead.** `metric: faithfulness and relevance scores`, `threshold: faithfulness >= 0.90, relevance >= 0.85 on 100 frozen cases`, `verification: scripts/eval_replay.py; CI semantic gate blocks a prompt or model change when either threshold is missed`.

**Note (added later, 16:40).** The "100 frozen cases" figure proved aspirational: the set closed at 25 (DEBT-02). The threshold numbers held; the corpus size did not. See T5 for how we handled the gap — by amending the criterion rather than pretending.

### [10:41] Agent — MoSCoW pass

> All 24 requirements marked `must`, since all are required by the spec.

### [10:43] Human intervention — **REJECT**

> If everything is MUST, the prioritisation carries no information and the required "tradeoff statement" becomes fiction. Decide what we will drop under pressure.

**Why.** The spec asks for MoSCoW *and* an explicit tradeoff. A list where nothing can be dropped is a list that will be dropped arbitrarily at 2am.

**Instead.** MUST = every invariant-bearing behaviour plus its verification surface (15 reqs). SHOULD = advisory quality, latency, cost (5). COULD = hot reload, multi-tenant audit view (2). WON'T = multi-language intake, LLM-signed verdicts, autonomous prescribing — with the reason stated once, in `prioritisation.tradeoff`: *breadth is traded for provability; anything that cannot be enumerated in a frozen fixture corpus is out of scope.*

### [11:05] Agent — wrote the registry, ran the gate

```
$ python scripts/validate_requirements.py
FAIL: 1 problem(s) in requirements.yaml
  - schema: requirements/15/fit_criterion: 'p95 <= 50 ms.' is too short
```

Agent proposed shortening the message by raising `minLength` to 10.

### [11:08] Human intervention — **REDIRECT**

> The gate is right and the message is incidental. `p95 <= 50 ms.` names a number and nothing else: not what is measured, not on what corpus, not where the result is reported. Fix the requirement, not the schema.

**Instead.**

```
Measured p95 adjudicate() latency over 1000 warm-table cases is <= 50 ms on the
CI runner, reported by the benchmark test in test/offline/.
```

**Why this is the interesting one.** The gate caught it by accident (`minLength: 20`), but the defect was semantic. We adopted the rule in `verification-constraints.md` §1: a fit criterion must contain a quantity **and** a measurement site. This is BUG-0001.

### [11:22] Agent — self-check

```
$ python scripts/validate_requirements.py
PASS: 24 requirements (5 invariants) validate against req-schema.json
```

### [11:26] Human — **APPROVE**

Approved with one condition: the registry is not frozen. Any later change must update `last_updated`, and `.agent/rules.md` §5 makes a rule that is more than one sprint stale a defect.

---

## Outcome

| Item | Result |
|---|---|
| Artefacts | `docs/req/requirements.yaml` (rev 1), `docs/req/req-schema.json`, `scripts/validate_requirements.py` |
| Requirements | 24 total: 8 functional, 5 invariant, 2 quality, 2 performance, 1 cost, 2 security, 4 governance |
| Gates at end | gate 3 PASS; other gates do not exist yet |
| What the human caught | a type that would have licensed trading a safety rule; an invariant that was unfalsifiable; a prioritisation that carried no information; a fit criterion that named a number instead of a measurement |
| What the human missed | that `REQ-Q-001`'s "100 frozen cases" was unachievable in the time available — discovered at T5 |
| Annotation count | 6 interventions: 1 CORRECT, 2 REJECT, 2 REDIRECT, 1 APPROVE |
