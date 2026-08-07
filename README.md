# Agentic Studio Digital Twin

> From vision to autonomous studio.

Agentic Studio Digital Twin is an AI-powered representation of a movie
production where autonomous AI agents collaborate to plan, monitor, explain,
and optimize filmmaking from script to release.

Instead of demonstrating only a chatbot, this project demonstrates a living
movie studio built around a shared Digital Twin.

## Core Vision

The platform models:

- Movies, scripts, scenes, and shots
- Actors, crew, locations, equipment, lighting, audio, and props
- Budgets, schedules, weather, and production status
- Editing, visual effects, marketing, and distribution

Each Digital Twin object can contain:

- Identity
- Metadata
- Relationships
- Current state
- History
- Events
- AI observations
- AI recommendations
- Human decisions

## Demonstration Story

A weather condition changes.

1. The Digital Twin receives the weather event.
2. The Scheduling Agent detects affected scenes and locations.
3. The Budget Agent calculates the financial impact.
4. The Producer Agent recommends options.
5. A human reviews and approves the decision.
6. The Digital Twin records the updated plan and audit history.

## Technology Direction

- Google Cloud
- Gemini (via `google-genai`)
- Google Cloud Agent Builder
- Parallel Search API (`parallel-web`) for live, grounded research
- Python and FastAPI backend
- React and TypeScript frontend
- Human-in-the-loop approvals
- Explainable AI recommendations
- Event-driven Digital Twin architecture

## Hackathon Track: Parallel

This project targets the **Parallel** track of the Google Cloud Agentic
Cinema Hackathon. The Research Agent (`src/agents/research_agent.py`) uses
the Parallel Search API at runtime to ground scheduling and budget decisions
in live, real-world information — for example, current weather conditions
at a shoot location, permit requirements, or comparable production costs —
before Gemini reasons over the result.

## Project Navigation

- [Vision](docs/vision/Vision.md)
- [Mission](docs/vision/Mission.md)
- [Roadmap](docs/roadmap/Production_Roadmap.md)
- [Enterprise Architecture](docs/architecture/EnterpriseArchitecture.md)
- [AI Agent Architecture](docs/architecture/AIAgentArchitecture.md)
- [Digital Twin Architecture](docs/architecture/DigitalTwinArchitecture.md)
- [Digital Twin Overview](docs/digital-twin/DigitalTwinOverview.md)
- [Developer Onboarding](docs/onboarding/NewDeveloperGuide.md)
- [Mentor Guide](docs/onboarding/MentorGuide.md)
- [Project Check-Off Sheet](PROJECT_CHECKLIST.md)
- [Project Manager Audit](reports/PROJECT_MANAGER_AUDIT.md)

## Repository Layout

```text
Agentic-Cinema/
├── docs/
├── diagrams/
├── images/
├── examples/
├── templates/
├── presentations/
├── src/
├── tests/
├── scripts/
├── reports/
└── .github/
```

## Local Bootstrap

```powershell
python .\bootstrap_agentic_studio_v2.py create
python .\bootstrap_agentic_studio_v2.py audit
python .\bootstrap_agentic_studio_v2.py health
```

## Project Status

Run the repository manager to regenerate the checklist, health report,
maturity score, and project-manager recommendations.

## License

See [LICENSE](LICENSE).
