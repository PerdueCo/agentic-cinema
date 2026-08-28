"""Research Agent.

Grounds the Digital Twin's decisions in live, real-world information.

Runtime dependencies (both called, not just referenced):
  - Parallel Search API, via the official `parallel-web` SDK      -> satisfies
    the Parallel track requirement.
  - Gemini, via `google-genai`                                    -> satisfies
    the Google Cloud AI requirement.

Flow for the weather-disruption demo story:
  1. A WeatherDisruptionEvent arrives (e.g. from a webhook or the CLI demo).
  2. This agent issues a live Parallel search for current conditions and any
     relevant advisories at the shoot location.
  3. Gemini summarizes the raw search result into a short, decision-ready
     brief that the Scheduling Agent consumes next.

Run directly for a smoke test:
    python -m src.agents.research_agent
"""

from __future__ import annotations

import asyncio
import logging
import os

from parallel import AsyncParallel
from google import genai

from src.shared.schemas import ResearchFinding, SceneLocation, WeatherDisruptionEvent

logger = logging.getLogger(__name__)

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")


class ResearchAgent:
    """Turns a raw event into a grounded, Gemini-summarized research finding."""

    def __init__(
        self,
        parallel_api_key: str | None = None,
        gemini_client: genai.Client | None = None,
    ) -> None:
        self._parallel = AsyncParallel(
            api_key=parallel_api_key or os.environ["PARALLEL_API_KEY"]
        )
        if gemini_client is not None:
            self._gemini = gemini_client
        else:
            self._gemini = genai.Client(
                vertexai=True,
                project=os.environ["GOOGLE_CLOUD_PROJECT"],
                location=os.environ.get("GOOGLE_CLOUD_LOCATION", "global"),
            )

    async def investigate(self, event: WeatherDisruptionEvent) -> ResearchFinding:
        """Run a live Parallel search and summarize it with Gemini."""
        query = (
            f"current weather and any filming advisories or road/permit "
            f"impacts in {event.location.city}, {event.location.country} "
            f"around {event.scheduled_date}"
        )

        # --- Parallel Search API call (runtime, not just README mention) ---
        search_result = await self._parallel.search(
            objective=query,
            search_queries=[query],
            mode="turbo",
            max_chars_total=6000,
        )

        top_result = search_result.results[0] if search_result.results else None
        raw_excerpt = top_result.excerpts[0] if top_result and top_result.excerpts else ""
        source_url = top_result.url if top_result else None

        # --- Gemini call (runtime, not just README mention) -----------------
        response = self._gemini.models.generate_content(
            model=GEMINI_MODEL,
            contents=(
                "Summarize this search result in 2 sentences for a film "
                "production Scheduling Agent. Focus only on facts relevant "
                f"to whether shooting can proceed as planned.\n\n{raw_excerpt}"
            ),
        )
        summary = response.text.strip() if response.text else "No summary available."

        finding = ResearchFinding(
            query=query,
            summary=summary,
            source_url=source_url,
            excerpt=raw_excerpt or None,
        )
        logger.info("Research finding for %s: %s", event.location.name, summary)
        return finding


async def _demo() -> None:
    """Smoke test using the weather-event demo scenario from the README."""
    logging.basicConfig(level=logging.INFO)

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

    agent = ResearchAgent()
    finding = await agent.investigate(event)
    print(finding)


if __name__ == "__main__":
    asyncio.run(_demo())
