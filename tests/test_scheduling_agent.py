"""Unit test for SchedulingAgent.recommend.

The Gemini call is mocked so this runs in CI without a real API key. The
point of this test is to lock in the contract: given a research finding
that mentions a storm, the agent returns a ScheduleRecommendation whose
action and reasoning came straight from Gemini's response, carrying the
event's affected scene IDs through unchanged.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from src.agents.scheduling_agent import SchedulingAgent
from src.shared.schemas import ResearchFinding, SceneLocation, WeatherDisruptionEvent


def test_recommend_returns_action_and_reasoning_from_gemini():
    agent = SchedulingAgent(gemini_api_key="test")

    fake_response = SimpleNamespace(
        text="RESCHEDULE\nExterior shots are unsafe during an active storm warning."
    )
    agent._gemini.models.generate_content = MagicMock(return_value=fake_response)

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
    finding = ResearchFinding(
        query="storm warning Big Sur",
        summary="A storm warning is active near the shoot location.",
        source_url="https://example.com/weather",
        excerpt="Storm warning issued for the Big Sur coastline.",
    )

    recommendation = agent.recommend(event, finding)

    assert recommendation.suggested_action == "reschedule"
    assert "unsafe" in recommendation.reasoning.lower()
    assert recommendation.affected_scene_ids == ["scene-014", "scene-015"]
    agent._gemini.models.generate_content.assert_called_once()