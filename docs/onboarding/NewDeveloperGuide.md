# New Developer Guide

Welcome to Agentic Studio Digital Twin. This guide gets you from clone to
running your first agent.

## What this project is

An AI-powered Digital Twin of a movie production. Autonomous agents
(Research, Scheduling, Budget, Producer) collaborate around a shared state
object to plan, monitor, and recommend decisions — with a human approving
before anything takes effect. See [Vision](../vision/Vision.md) for the full
pitch and [Cloud Architecture](../architecture/CloudArchitecture.md) for how
the pieces fit together.

## Setup

Follow [Environment Setup](EnvironmentSetup.md) first if you haven't
installed dependencies yet. Short version:

```bash
git clone https://github.com/PerdueCo/agentic-cinema.git
cd agentic-cinema
pip install -r requirements.txt
cp .env.example .env   # then fill in GEMINI_API_KEY and PARALLEL_API_KEY
```

## Run your first agent

The Research Agent is the one fully working piece right now. It calls the
Parallel Search API for live information, then Gemini to summarize it:

```bash
python -m src.agents.research_agent
```

This runs a demo scenario (a storm warning near a Big Sur shoot location)
and prints a `ResearchFinding` with a summary and a source URL.

## Run the tests

```bash
pytest tests/ -q
```

`tests/test_research_agent.py` mocks both external API calls, so it runs
without real API keys — useful for CI and for anyone who hasn't set up
credentials yet.

## Codebase map

| Path | What's there |
|---|---|
| `src/agents/` | One agent per file. `research_agent.py` is the only one implemented so far. |
| `src/shared/schemas.py` | Shared dataclasses (`SceneLocation`, `ResearchFinding`, `WeatherDisruptionEvent`) every agent reads and writes. |
| `src/backend/`, `src/frontend/`, `src/digital_twin/` | Not yet implemented — placeholders for the FastAPI backend and React frontend. |
| `tests/` | Pytest, mocked, no live keys required. |
| `docs/` | Vision, architecture, roadmap, and onboarding docs (this file included). |

## A good first task

Implement the **Scheduling Agent** (`src/agents/scheduling_agent.py`,
currently doesn't exist yet). It should:

1. Accept a `ResearchFinding` from the Research Agent.
2. Determine which scenes/locations are affected, using
   `WeatherDisruptionEvent.location.scene_ids`.
3. Return a structured recommendation (new dataclass in `schemas.py`) that
   the Budget Agent can consume next.

Follow the pattern in `research_agent.py`: a typed input, a typed output, a
docstring explaining *why*, and a mocked unit test.

## Pull requests

1. Branch off `main`.
2. Keep PRs scoped to one agent or one concern — small and reviewable.
3. Include or update a test for anything in `src/`.
4. Run `pytest tests/ -q` before opening the PR.
5. Note in the PR description which part of the Demonstration Story
   (see root README) your change moves forward.