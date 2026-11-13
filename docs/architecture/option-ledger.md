# Option Ledger

Rejected options are not deleted — they are parked with **the condition that would bring them back**. A rejected option with no trigger is a decision made on vibes; a rejected option with a trigger is a decision that can be revisited on evidence.

| # | Option | Rejected because | Reconsider when | Cost to revisit |
|---|---|---|---|---|
| O-1 | Single model call returns the verdict (A1) | No invariant is provable offline; INV-001/002/003 become unfalsifiable | Never for a safety verdict. Would only return if the product changed to a **non-safety** advisory tool where a wrong answer costs nothing | low (smaller codebase) |
| O-2 | LLM panel / judge ensemble (A2) | 3× cost breaks REQ-C-001; correlated errors mean agreement is not verification | If pricing drops ~10× **and** a requirement demands a confidence score rather than a categorical verdict | medium |
| O-3 | RAG over interaction tables as the decision path (A3) | Retrieval misses are silent false negatives — worst failure under driver D1 | If a requirement needs open-world drug coverage that a closed table cannot hold, use RAG to *propose table rows for human signing*, never to decide at runtime | medium |
| O-4 | Vector store over past cases for "similar case" retrieval | Creates a second, unaudited copy of PHI (INV-004); also makes verdicts path-dependent on history | Only with a documented de-identification pipeline and a retention policy approved by review. Not for this course | high |
| O-5 | Fine-tuned classifier for the verdict (A5) | No labelled corpus, no annotation budget; still probabilistic | If a labelled dataset of ≥ 5k adjudicated cases becomes available and a calibrated risk score is required | high |
| O-6 | Separate microservices per component | Operational overhead with no benefit at this scale; complicates offline CI (driver D6) | If components need independent deployment or different scaling profiles | medium |
| O-7 | Relational DB (SQLite/Postgres) for audit instead of JSONL | Concurrency we do not have; migration overhead; JSONL is diffable and hash-chainable with stdlib only | If multiple concurrent reviewers write overrides, or audit volume exceeds ~10⁵ records | low |
| O-8 | Let the model produce the normalized dose (structured output) | Dose is an authority field (INV-003); normalization is a deterministic table lookup, cheaper and testable | Never — this is an invariant, not a preference | n/a |
| O-9 | Agent-authored ADRs to speed up the build | An agent that writes its own constraints has none (permission model §5) | Never | n/a |
| O-10 | Skipping the semantic evaluation gate to save CI minutes | Gate 4 is required by D7; without it prompt changes ship unmeasured | Never | n/a |
| O-11 | Truncating over-long case notes to fit the token budget | Silent truncation can drop a medication → violates the spirit of INV-001 and fails closed only by luck | Never; escalate with `CASE_TOO_LARGE` instead | n/a |
| O-12 | Treating `HOLD` as an error state to be "fixed" by tuning | `HOLD` is the designed safe outcome; tuning it away converts safety into throughput | If gap rate > 20%, fix **coverage**, not the verdict policy | n/a |

**Reading rule:** rows marked "Never" are locked by an invariant or a driver. They are listed so that a future reader does not re-litigate them as if they were open questions; changing one requires an ADR that names the driver it moves, not a code change.
