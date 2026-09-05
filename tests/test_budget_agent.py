"""Unit test for BudgetAgent.assess.

The Gemini call is mocked so this runs in CI without a real API key. The
point of this test is to lock in the contract: given a scheduling
recommendation to reschedule, the agent returns a BudgetAssessment whose
cost range, action, and reasoning came straight from Gemini's response.
"""

from __future__ import annotations

import os
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src.agents.budget_agent import BudgetAgent
from src.shared.schemas import ScheduleRecommendation, SceneLocation, WeatherDisruptionEvent


def test_historical_budget_prompt_is_advisory_and_preserves_generated_output():
    client = MagicMock()
    client.models.generate_content.return_value = SimpleNamespace(text="$10,000-$30,000\nAPPROVE\nPlanning estimate only.")
    event = WeatherDisruptionEvent(
        location=SceneLocation("scene-42-location", "Exterior", "Atlanta", "USA", ["scene-42"]),
        condition="EF2 tornado", scheduled_date="2008-03-14", evidence_mode="historical_replay",
    )
    schedule = ScheduleRecommendation(["scene-42"], "Historical scenario", "reschedule")
    result = BudgetAgent(gemini_client=client).assess(event, schedule)
    prompt = client.models.generate_content.call_args.kwargs["contents"]
    assert "2008-03-14" in prompt and "historical_replay" in prompt
    assert "not an authorization or an approved expenditure" in prompt
    assert "not a quote" in prompt
    assert result.estimated_cost_impact == "$10,000-$30,000"
    assert result.recommended_action == "approve"
    assert result.reasoning == "Planning estimate only."


def test_budget_agent_default_vertex_client(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-project")
    monkeypatch.setenv("GOOGLE_CLOUD_LOCATION", "us-east1")
    with patch("google.genai.Client") as mock_client_class:
        _ = BudgetAgent()
        mock_client_class.assert_called_once_with(
            vertexai=True,
            project="test-project",
            location="us-east1",
        )


def test_assess_returns_cost_range_action_and_reasoning_from_gemini():
    mock_client = MagicMock()
    fake_response = SimpleNamespace(
        text=(
            "$3,000-$5,000\n"
            "ESCALATE\n"
            "Rescheduling a two-scene exterior shoot requires producer sign-off."
        )
    )
    mock_client.models.generate_content.return_value = fake_response

    agent = BudgetAgent(gemini_client=mock_client)

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
    recommendation = ScheduleRecommendation(
        affected_scene_ids=["scene-014", "scene-015"],
        reasoning="Exterior shots are unsafe during an active storm warning.",
        suggested_action="reschedule",
    )

    assessment = agent.assess(event, recommendation)

    assert assessment.estimated_cost_impact == "$3,000-$5,000"
    assert assessment.recommended_action == "escalate"
    assert "sign-off" in assessment.reasoning.lower()
    mock_client.models.generate_content.assert_called_once()
