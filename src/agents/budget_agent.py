"""Budget Agent.

Takes the Scheduling Agent's recommendation and estimates the financial
impact, producing a structured assessment a human can approve or escalate.

Runtime dependency (called, not just referenced):
  - Gemini, via `google-genai` -> satisfies the Google Cloud AI requirement.

Flow:
  1. Accepts the WeatherDisruptionEvent and the ScheduleRecommendation the
     Scheduling Agent already produced for it.
  2. Asks Gemini to estimate the cost impact of that recommendation and
     decide: APPROVE (small, routine cost), ESCALATE (needs producer
     sign-off), or DECLINE (too costly, send back to Scheduling).
  3. Returns a BudgetAssessment the Producer Agent can act on next.

This agent is deliberately honest about its limits: without real day-rate
or crew-size data wired in yet, its cost estimate is Gemini's informed
judgment from the finding text alone, not a calculation from real numbers.
The `estimated_cost_impact` field stays a descriptive string for exactly
that reason â€” see the docstring on BudgetAssessment in schemas.py.

Run directly for a smoke test, chaining off live Research + Scheduling
Agent calls:
    python -m src.agents.budget_agent
"""

from __future__ import annotations

import asyncio
import logging
import os

from google import genai

from src.shared.schemas import (
    BudgetAssessment,
    ResearchFinding,
    ScheduleRecommendation,
    SceneLocation,
    WeatherDisruptionEvent,
)

logger = logging.getLogger(__name__)

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")


class BudgetAgent:
    """Turns a scheduling recommendation into a cost-impact assessment."""

    def __init__(self, gemini_client: genai.Client | None = None) -> None:
        if gemini_client is not None:
            self._gemini = gemini_client
        else:
            self._gemini = genai.Client(
                vertexai=True,
                project=os.environ["GOOGLE_CLOUD_PROJECT"],
                location=os.environ.get("GOOGLE_CLOUD_LOCATION", "global"),
            )

    def assess(
        self,
        event: WeatherDisruptionEvent,
        recommendation: ScheduleRecommendation,
    ) -> BudgetAssessment:
        """Estimate cost impact and decide APPROVE / ESCALATE / DECLINE."""
        prompt = (
            "You are a film production Budget Agent. Given a scheduling "
            "decision, estimate the likely cost impact as a rough dollar "
            "range, then decide whether a human producer should APPROVE "
            "this cost as routine, ESCALATE it for sign-off, or DECLINE "
            "and send it back to Scheduling for a cheaper option. Respond "
            "in exactly three lines: the dollar range, the decision word "
            "alone, then a one-sentence rationale. Nothing else.\n\n"
            f"Location: {event.location.name}\n"
            f"Affected scenes: {', '.join(recommendation.affected_scene_ids) or 'none listed'}\n"
            f"Scheduling decision: {recommendation.suggested_action.upper()}\n"
            f"Scheduling rationale: {recommendation.reasoning}"
        )

        # --- Gemini call (runtime, not just README mention) -----------------
        response = self._gemini.models.generate_content(
            model=GEMINI_MODEL, contents=prompt
        )
        text = (response.text or "").strip()
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        cost_range = lines[0] if lines else "unknown"
        action = lines[1].lower() if len(lines) > 1 else "escalate"
        reasoning = lines[2] if len(lines) > 2 else text

        assessment = BudgetAssessment(
            estimated_cost_impact=cost_range,
            reasoning=reasoning,
            recommended_action=action,
        )
        logger.info(
            "Budget assessment for %s: %s (%s)",
            event.location.name,
            action,
            cost_range,
        )
        return assessment


async def _demo() -> None:
    """Smoke test: real Research + Scheduling output feeding the Budget Agent."""
    logging.basicConfig(level=logging.INFO)

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
    recommendation = scheduling_agent.recommend(event, finding)

    budget_agent = BudgetAgent()
    assessment = budget_agent.assess(event, recommendation)
    print(assessment)


if __name__ == "__main__":
    asyncio.run(_demo())
