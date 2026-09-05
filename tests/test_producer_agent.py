"""Unit test for ProducerAgent.recommend.

The Gemini call is mocked so this runs in CI without a real API key. The
point of this test is to lock in the contract: given a finding, a
scheduling decision, and a budget assessment, the agent returns a
ProducerRecommendation whose decision, summary, and rationale came
straight from Gemini's synthesis of all three inputs.
"""

from __future__ import annotations

import os
import pytest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src.agents.producer_agent import ProducerAgent
from src.shared.schemas import (
    BudgetAssessment,
    ResearchFinding,
    ScheduleRecommendation,
    SceneLocation,
    WeatherDisruptionEvent,
)


def test_producer_agent_default_vertex_client(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-project")
    monkeypatch.setenv("GOOGLE_CLOUD_LOCATION", "us-east1")
    with patch("google.genai.Client") as mock_client_class:
        _ = ProducerAgent()
        mock_client_class.assert_called_once_with(
            vertexai=True,
            project="test-project",
            location="us-east1",
        )


@pytest.mark.parametrize("action,decision", [
    ("reschedule", "Reschedule production"),
    ("relocate", "Relocate production"),
    ("proceed", "Proceed with filming — no conflict exists."),
])
def test_replay_prompt_preserves_summary_rationale_and_decision_rules(action, decision):
    client = MagicMock()
    client.models.generate_content.return_value = SimpleNamespace(
        text="Proceed with filming — no conflict exists.\nOriginal summary.\nOriginal rationale."
    )
    event = WeatherDisruptionEvent(
        location=SceneLocation("scene-42-location", "Exterior", "Atlanta", "USA", ["scene-42"]),
        condition="EF2 tornado", scheduled_date="2008-03-14", evidence_mode="historical_replay",
    )
    finding = ResearchFinding("Historical query", "Candidate evidence", "https://example.com", "Historical excerpt")
    schedule = ScheduleRecommendation(["scene-42"], "Scenario reasoning", action)
    budget = BudgetAssessment("$10,000-$30,000", "Estimate", "approve")
    result = ProducerAgent(gemini_client=client).recommend(event, finding, schedule, budget)
    prompt = client.models.generate_content.call_args.kwargs["contents"]
    assert "2008-03-14" in prompt and "historical_replay" in prompt
    assert "not human authorization" in prompt
    assert "never approved adjustment costs" in prompt
    assert finding.excerpt in prompt
    assert result.final_decision == decision
    assert result.summary == "Original summary."
    assert result.rationale == "Original rationale."
    if action != "proceed":
        assert "proceed" not in result.final_decision.lower()


def test_recommend_synthesizes_all_three_inputs_via_gemini():
    mock_client = MagicMock()
    fake_response = SimpleNamespace(
        text=(
            "Reschedule and escalate budget for sign-off\n"
            "A storm warning threatens two exterior scenes at the Big Sur set.\n"
            "Rescheduling avoids unsafe conditions but requires producer "
            "approval given the added cost."
        )
    )
    mock_client.models.generate_content.return_value = fake_response

    agent = ProducerAgent(gemini_client=mock_client)

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
    schedule = ScheduleRecommendation(
        affected_scene_ids=["scene-014", "scene-015"],
        reasoning="Exterior shots are unsafe during an active storm warning.",
        suggested_action="reschedule",
    )
    budget = BudgetAssessment(
        estimated_cost_impact="$3,000-$5,000",
        reasoning="Rescheduling a two-scene exterior shoot requires producer sign-off.",
        recommended_action="escalate",
    )

    recommendation = agent.recommend(event, finding, schedule, budget)

    assert "reschedule" in recommendation.final_decision.lower()
    assert "storm" in recommendation.summary.lower()
    assert "approval" in recommendation.rationale.lower()
    mock_client.models.generate_content.assert_called_once()
