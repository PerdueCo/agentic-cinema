# Cloud Architecture

This project targets the **Parallel track** of the Google Cloud Agentic
Cinema Hackathon. Two runtime dependencies are actually called in the code
today (see `src/agents/research_agent.py`) — everything else below is
architecture direction for what's built next.

## In use today

- **Gemini** — called via the `google-genai` SDK. Used to turn raw search
  results into short, decision-ready summaries for downstream agents.
- **Parallel Search API** — called via the `parallel-web` SDK. Provides
  live, sourced web results (e.g. current weather, advisories) so agent
  recommendations are grounded in real information rather than model
  training data. This satisfies the hackathon's Parallel track requirement.

## Planned

- **Google Cloud Agent Builder** — to orchestrate the multi-agent pipeline
  (Research → Scheduling → Budget → Producer) as the number of agents
  grows beyond direct function calls between them.
- **FastAPI backend** (`src/backend/`, not yet implemented) — to expose the
  Digital Twin's state and agent outputs to the frontend.
- **React + TypeScript frontend** (`src/frontend/`, not yet implemented) —
  to visualize the Digital Twin and present agent recommendations for
  human-in-the-loop approval.
- **Google Cloud hosting** — target deployment platform (e.g. Cloud Run)
  once the backend exists, to get a hosted project URL for submission.

## Data flow (weather-disruption demo)

1. A `WeatherDisruptionEvent` is created (currently via the CLI demo in
   `research_agent.py`; later, via a webhook or scheduled check).
2. **Research Agent** calls Parallel Search for live conditions at the
   shoot location, then Gemini to summarize the result into a
   `ResearchFinding`.
3. **Scheduling Agent** *(not yet implemented)* determines which scenes and
   locations are affected.
4. **Budget Agent** *(not yet implemented)* calculates financial impact.
5. **Producer Agent** *(not yet implemented)* turns the above into a
   recommendation.
6. A human reviews and approves the recommendation.
7. The Digital Twin records the decision and its audit history.

Every finding carries its source URL through the pipeline, so a human
reviewing the final recommendation can verify it against the original data
rather than trusting the agent's summary blindly.

## Not in use

IBM Bob and Confluent were part of an earlier technology direction when
this project was considering the IBM track. The project has since committed
to the Parallel track — see the [README](../../README.md#hackathon-track-parallel)
for the current direction.