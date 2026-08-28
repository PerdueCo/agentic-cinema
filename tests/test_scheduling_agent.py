"""Unit test for SchedulingAgent.recommend.

The Gemini call is mocked so this runs in CI without a real API key. The
point of this test is to lock in the contract: given a research finding
that mentions a storm, the agent returns a ScheduleRecommendation whose
action and reasoning came straight from Gemini's response, carrying the
event's affected scene IDs through unchanged.
"""

from __future__ import annotations

import os
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src.agents.scheduling_agent import SchedulingAgent
from src.shared.schemas import ResearchFinding, SceneLocation, WeatherDisruptionEvent


def test_scheduling_agent_default_vertex_client(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-project")
    monkeypatch.setenv("GOOGLE_CLOUD_LOCATION", "us-east1")
    with patch("google.genai.Client") as mock_client_class:
        _ = SchedulingAgent()
        mock_client_class.assert_called_once_with(
            vertexai=True,
            project="test-project",
            location="us-east1",
        )


def test_recommend_returns_action_and_reasoning_from_gemini():
    mock_client = MagicMock()
    fake_response = SimpleNamespace(
        text="RESCHEDULE\nExterior shots are unsafe during an active storm warning."
    )
    mock_client.models.generate_content.return_value = fake_response

    agent = SchedulingAgent(gemini_client=mock_client)

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
    mock_client.models.generate_content.assert_called_once()
