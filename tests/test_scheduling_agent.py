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


def test_scheduling_agent_severe_weather_triggers():
    """Verify deterministic severe event detection across all criteria."""
    cases = [
        # condition "severe weather"
        {"condition": "severe weather", "raw_payload": {}, "is_severe": True},
        # condition "severe storm"
        {"condition": "severe storm", "raw_payload": {}, "is_severe": True},
        # rain heavy
        {"condition": "rainy", "raw_payload": {"rain": "heavy"}, "is_severe": True},
        {"condition": "rainy", "raw_payload": {"rain": "Heavy"}, "is_severe": True},
        # wind >= 30
        {"condition": "windy", "raw_payload": {"wind_mph": 30}, "is_severe": True},
        {"condition": "windy", "raw_payload": {"wind_mph": "35"}, "is_severe": True},
        # lightning_risk high
        {"condition": "thunder", "raw_payload": {"lightning_risk": "high"}, "is_severe": True},
        {"condition": "thunder", "raw_payload": {"lightning_risk": "High"}, "is_severe": True},
        # medium lightning risk - NOT severe
        {"condition": "thunder", "raw_payload": {"lightning_risk": "medium"}, "is_severe": False},
        # wind < 30 - NOT severe
        {"condition": "windy", "raw_payload": {"wind_mph": 25}, "is_severe": False},
        # light rain - NOT severe
        {"condition": "rainy", "raw_payload": {"rain": "light"}, "is_severe": False},
    ]

    location = SceneLocation(
        location_id="loc-001",
        name="Coastal Cliff Set",
        city="Big Sur",
        country="USA",
        scene_ids=["scene-014"],
    )
    finding = ResearchFinding(
        query="Big Sur weather",
        summary="Supporting research finding.",
        source_url="https://example.com/weather",
        excerpt="Supporting weather details.",
    )

    for case in cases:
        mock_client = MagicMock()
        fake_response = SimpleNamespace(
            text="PROCEED\nProceed as scheduled."
        )
        mock_client.models.generate_content.return_value = fake_response
        agent = SchedulingAgent(gemini_client=mock_client)

        event = WeatherDisruptionEvent(
            location=location,
            condition=case["condition"],
            scheduled_date="2026-09-12",
            raw_payload=case["raw_payload"],
        )

        recommendation = agent.recommend(event, finding)

        if case["is_severe"]:
            assert recommendation.suggested_action == "relocate"
            assert recommendation.reasoning.startswith("Evidence conflict:")
        else:
            assert recommendation.suggested_action == "proceed"
            assert not recommendation.reasoning.startswith("Evidence conflict:")


def test_scheduling_severe_event_favorable_research_optimistic_gemini():
    """severe event plus favorable research and an optimistic Gemini response"""
    mock_client = MagicMock()
    fake_response = SimpleNamespace(
        text="PROCEED\nThe crew can proceed safely."
    )
    mock_client.models.generate_content.return_value = fake_response

    agent = SchedulingAgent(gemini_client=mock_client)

    location = SceneLocation(
        location_id="loc-001",
        name="Coastal Cliff Set",
        city="Big Sur",
        country="USA",
        scene_ids=["scene-014"],
    )
    # Severe event: wind_mph is 35 (at least 30)
    event = WeatherDisruptionEvent(
        location=location,
        condition="windy",
        scheduled_date="2026-09-12",
        raw_payload={"wind_mph": 35},
    )
    # Favorable research
    finding = ResearchFinding(
        query="Big Sur weather",
        summary="Favorable research: storm has completely passed.",
        source_url="https://example.com/weather",
        excerpt="Clear skies ahead.",
    )

    recommendation = agent.recommend(event, finding)

    # Should override to relocate and prepends Evidence conflict:
    assert recommendation.suggested_action == "relocate"
    assert recommendation.reasoning.startswith("Evidence conflict:")
    assert "proceed safely" in recommendation.reasoning


def test_scheduling_severe_event_unexpected_gemini_action():
    """severe event plus unexpected Gemini action (e.g. CONTINUE)"""
    mock_client = MagicMock()
    fake_response = SimpleNamespace(
        text="CONTINUE\nThe external research appears favorable."
    )
    mock_client.models.generate_content.return_value = fake_response

    agent = SchedulingAgent(gemini_client=mock_client)

    location = SceneLocation(
        location_id="loc-001",
        name="Coastal Cliff Set",
        city="Big Sur",
        country="USA",
        scene_ids=["scene-014"],
    )
    # Severe event: wind_mph is 35 (at least 30)
    event = WeatherDisruptionEvent(
        location=location,
        condition="windy",
        scheduled_date="2026-09-12",
        raw_payload={"wind_mph": 35},
    )
    # Favorable research
    finding = ResearchFinding(
        query="Big Sur weather",
        summary="Favorable research: storm has completely passed.",
        source_url="https://example.com/weather",
        excerpt="Clear skies ahead.",
    )

    recommendation = agent.recommend(event, finding)

    # Fail-safe override: unexpected actions on severe events must revert to relocate
    assert recommendation.suggested_action == "relocate"
    assert recommendation.reasoning.startswith("Evidence conflict:")
    assert "external research" in recommendation.reasoning.lower()


def test_scheduling_severe_event_severe_research():
    """severe event plus severe research"""
    mock_client = MagicMock()
    fake_response = SimpleNamespace(
        text="RELOCATE\nRelocate because of the extreme wind risk."
    )
    mock_client.models.generate_content.return_value = fake_response

    agent = SchedulingAgent(gemini_client=mock_client)

    location = SceneLocation(
        location_id="loc-001",
        name="Coastal Cliff Set",
        city="Big Sur",
        country="USA",
        scene_ids=["scene-014"],
    )
    # Severe event: condition contains severe storm
    event = WeatherDisruptionEvent(
        location=location,
        condition="severe storm warning",
        scheduled_date="2026-09-12",
        raw_payload={},
    )
    # Severe research
    finding = ResearchFinding(
        query="Big Sur weather",
        summary="Severe research: hurricane-force winds expected.",
        source_url="https://example.com/weather",
        excerpt="Extreme weather warning.",
    )

    recommendation = agent.recommend(event, finding)

    # Should preserve Gemini's relocate and not prepended with Evidence conflict:
    assert recommendation.suggested_action == "relocate"
    assert not recommendation.reasoning.startswith("Evidence conflict:")
    assert "extreme wind risk" in recommendation.reasoning


def test_scheduling_favorable_event_favorable_research():
    """favorable event plus favorable research"""
    mock_client = MagicMock()
    fake_response = SimpleNamespace(
        text="PROCEED\nSunny conditions, proceed as scheduled."
    )
    mock_client.models.generate_content.return_value = fake_response

    agent = SchedulingAgent(gemini_client=mock_client)

    location = SceneLocation(
        location_id="loc-001",
        name="Coastal Cliff Set",
        city="Big Sur",
        country="USA",
        scene_ids=["scene-014"],
    )
    # Favorable event
    event = WeatherDisruptionEvent(
        location=location,
        condition="sunny",
        scheduled_date="2026-09-12",
        raw_payload={"wind_mph": 5, "lightning_risk": "low"},
    )
    # Favorable research
    finding = ResearchFinding(
        query="Big Sur weather",
        summary="Sunny and calm weather.",
        source_url="https://example.com/weather",
        excerpt="Zero chance of rain.",
    )

    recommendation = agent.recommend(event, finding)

    # Should remain proceed
    assert recommendation.suggested_action == "proceed"
    assert not recommendation.reasoning.startswith("Evidence conflict:")
    assert "proceed as scheduled" in recommendation.reasoning
