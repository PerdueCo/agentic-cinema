"""Scheduling Agent.

Determines what should happen to affected scenes given a grounded research
finding, and produces a structured recommendation for the Budget Agent.

Runtime dependency (called, not just referenced):
  - Gemini, via `google-genai` -> satisfies the Google Cloud AI requirement.

Flow:
  1. Accepts the WeatherDisruptionEvent (for its location and affected
     scene IDs) and the ResearchFinding the Research Agent already produced
     for that event.
  2. Asks Gemini to reason over the grounded finding and decide: PROCEED,
     RESCHEDULE, or RELOCATE, with a one-sentence rationale.
  3. Returns a ScheduleRecommendation the Budget Agent can price out next.

This agent never invents facts about conditions on the ground itself â€” it
only reasons over what the Research Agent already grounded with a real
source. That separation of concerns (one agent grounds, the next reasons)
is the pattern the rest of the ecosystem follows.

Run directly for a smoke test, chaining off a live Research Agent call:
    python -m src.agents.scheduling_agent
"""

from __future__ import annotations

import asyncio
import logging
import os

from google import genai

from src.shared.schemas import (
    ResearchFinding,
    ScheduleRecommendation,
    SceneLocation,
    WeatherDisruptionEvent,
)

logger = logging.getLogger(__name__)

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")


class SchedulingAgent:
    """Turns a grounded research finding into a scene-level scheduling call."""

    def __init__(self, gemini_api_key: str | None = None) -> None:
        self._gemini = genai.Client(
            api_key=gemini_api_key or os.environ["GOOGLE_API_KEY"]
        )

    def recommend(
        self, event: WeatherDisruptionEvent, finding: ResearchFinding
    ) -> ScheduleRecommendation:
        """Decide PROCEED / RESCHEDULE / RELOCATE for the affected scenes."""
        scene_ids = event.location.scene_ids
        prompt = (
            "You are a film production Scheduling Agent. Given a grounded "
            "research finding, decide whether the crew should PROCEED, "
            "RESCHEDULE, or RELOCATE for the affected scenes. Respond with "
            "the decision word alone on the first line, then a one-sentence "
            "rationale on the second line. Nothing else.\n\n"
            f"Location: {event.location.name}\n"
            f"Affected scenes: {', '.join(scene_ids) or 'none listed'}\n"
            f"Finding: {finding.summary}"
        )

        # --- Gemini call (runtime, not just README mention) -----------------
        response = self._gemini.models.generate_content(
            model=GEMINI_MODEL, contents=prompt
        )
        text = (response.text or "").strip()
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        action = lines[0].lower() if lines else "proceed"
        reasoning = lines[1] if len(lines) > 1 else text

        recommendation = ScheduleRecommendation(
            affected_scene_ids=scene_ids,
            reasoning=reasoning,
            suggested_action=action,
        )
        logger.info(
            "Scheduling recommendation for %s: %s", event.location.name, action
        )
        return recommendation


async def _demo() -> None:
    """Smoke test: real Research Agent output feeding the Scheduling Agent."""
    logging.basicConfig(level=logging.INFO)

    from src.agents.research_agent import ResearchAgent

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
    print(recommendation)


if __name__ == "__main__":
    asyncio.run(_demo())
