# Decision Log

Record important architecture, product, scope, and team decisions.

---

## 2026-08-10 — Executive approval is a human action, not an AI agent

**Decision:** The final "Executive Approval" step in the weather-event demo
story (Weather → Digital Twin Update → Scheduling Agent → Budget Agent →
Producer Agent → Executive Approval → Digital Twin Updated → Audit Trail)
is a **human-in-the-loop action**, not an autonomous AI agent. There is no
`ExecutiveAgent` implementation planned for MVP.

**Context:** The pipeline already has four working agents — Research
(grounds the event in live data), Scheduling, Budget, and Producer (which
synthesizes the first three into one `ProducerRecommendation`). The
`ProducerRecommendation` is deliberately designed as "the one recommendation
a human actually reads and acts on" (see `src/shared/schemas.py`). Making
the Executive step an agent as well would mean an AI both proposes and
approves the final call, which undercuts the project's core "human
approval and creative control" commitment stated in `docs/vision/Mission.md`.

**What this means practically:**
- The Producer Agent's output is the last AI-generated artifact in the
  pipeline.
- "Executive Approval" is a person (e.g. a producer/exec role) reviewing
  the `ProducerRecommendation` — including its cited sources and
  reasoning — and approving, rejecting, or sending it back.
- That approval action, once approved or rejected, is what gets written to
  the Digital Twin's audit trail — not a model output.
- `docs/ai-agents/` intentionally does not and will not include an
  `ExecutiveAgent.md`. Judges/reviewers should not read its absence as a
  missing agent — it's a scope decision, documented here.

**Still open:** the concrete mechanism for that human action (a FastAPI
endpoint + minimal frontend approve/reject control) is not yet built —
see `docs/architecture/CloudArchitecture.md` "Planned" section and the
Digital Twin state/event store work.

**Status:** Decided. Revisit only if judging feedback or remaining time
suggests an "Executive Agent" would strengthen rather than dilute the
human-in-the-loop story.
