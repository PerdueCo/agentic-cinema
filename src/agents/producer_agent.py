"""Producer Agent.

Synthesizes the Research Agent's finding, the Scheduling Agent's decision,
and the Budget Agent's cost assessment into the one recommendation a human
actually reviews and approves.

Runtime dependency (called, not just referenced):
  - Gemini, via `google-genai` -> satisfies the Google Cloud AI requirement.

This is the agent that closes the loop described in the README's
Demonstration Story: the Digital Twin receives an event, three agents
reason about it in sequence, and the Producer Agent turns their combined
output into a single clear call for a human to approve — rather than
making the human read three separate agent outputs and synthesize them
by hand.

Run directly for a smoke test, chaining off live Research, Scheduling, and
Budget Agent calls:
    python -m src.agents.producer_agent
"""

from __future__ import annotations

import asyncio
import logging
import os

from google import genai

from src.shared.schemas import (
    BudgetAssessment,
    ProducerRecommendation,
    ResearchFinding,
    ScheduleRecommendation,
    SceneLocation,
    WeatherDisruptionEvent,
)

logger = logging.getLogger(__name__)

GEMINI_MODEL = "gemini-2.0-flash"


class ProducerAgent:
    """Turns three upstream agent outputs into one human-facing call."""

    def __init__(self, gemini_api_key: str | None = None) -> None:
        self._gemini = genai.Client(
            api_key=gemini_api_key or os.environ["GEMINI_API_KEY"]
        )

    def recommend(
        self,
        event: WeatherDisruptionEvent,
        finding: ResearchFinding,
        schedule: ScheduleRecommendation,
        budget: BudgetAssessment,
    ) -> ProducerRecommendation:
        """Synthesize the three upstream outputs into one final call."""
        prompt = (
            "You are a film production Producer Agent. Three specialists "
            "have already reported to you: a Research Agent, a Scheduling "
            "Agent, and a Budget Agent. Synthesize their input into one "
            "clear recommendation for a human producer to approve. Respond "
            "in exactly three lines: a short final decision phrase, a "
            "one-sentence summary of the situation, and a one-sentence "
            "rationale tying the three inputs together. Nothing else.\n\n"
            f"Location: {event.location.name}\n"
            f"Research finding: {finding.summary}\n"
            f"Scheduling decision: {schedule.suggested_action.upper()} "
            f"— {schedule.reasoning}\n"
            f"Budget assessment: {budget.recommended_action.upper()} "
            f"({budget.estimated_cost_impact}) — {budget.reasoning}"
        )

        # --- Gemini call (runtime, not just README mention) -----------------
        response = self._gemini.models.generate_content(
            model=GEMINI_MODEL, contents=prompt
        )
        text = (response.text or "").strip()
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        final_decision = lines[0] if lines else "Review required"
        summary = lines[1] if len(lines) > 1 else text
        rationale = lines[2] if len(lines) > 2 else summary

        recommendation = ProducerRecommendation(
            final_decision=final_decision,
            summary=summary,
            rationale=rationale,
        )
        logger.info(
            "Producer recommendation for %s: %s", event.location.name, final_decision
        )
        return recommendation


async def _demo() -> None:
    """Smoke test: the full chain, Research through Producer, live."""
    logging.basicConfig(level=logging.INFO)

    from src.agents.budget_agent import BudgetAgent
    from src.agents.research_agent import ResearchAgent
    from src.agents.scheduling_agent import SchedulingAgent

    location = SceneLocation(
        location_id="loc-001",
        name="Coastal Cliff Set",
        city="Big Sur",
        country="USA",
        scene_ids=["scene-014", "scene-015"],
    )
    event = WeatherDisruptionEvent(
        location=location,
        condition="storm warning",
        scheduled_date="2026-09-12",
    )

    research_agent = ResearchAgent()
    finding = await research_agent.investigate(event)

    scheduling_agent = SchedulingAgent()
    schedule = scheduling_agent.recommend(event, finding)

    budget_agent = BudgetAgent()
    budget = budget_agent.assess(event, schedule)

    producer_agent = ProducerAgent()
    recommendation = producer_agent.recommend(event, finding, schedule, budget)
    print(recommendation)


if __name__ == "__main__":
    asyncio.run(_demo())