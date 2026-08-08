"""Unit test for BudgetAgent.assess.

The Gemini call is mocked so this runs in CI without a real API key. The
point of this test is to lock in the contract: given a scheduling
recommendation to reschedule, the agent returns a BudgetAssessment whose
cost range, action, and reasoning came straight from Gemini's response.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from src.agents.budget_agent import BudgetAgent
from src.shared.schemas import ScheduleRecommendation, SceneLocation, WeatherDisruptionEvent


def test_assess_returns_cost_range_action_and_reasoning_from_gemini():
    agent = BudgetAgent(gemini_api_key="test")

    fake_response = SimpleNamespace(
        text=(
            "$3,000-$5,000\n"
            "ESCALATE\n"
            "Rescheduling a two-scene exterior shoot requires producer sign-off."
        )
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
    recommendation = ScheduleRecommendation(
        affected_scene_ids=["scene-014", "scene-015"],
        reasoning="Exterior shots are unsafe during an active storm warning.",
        suggested_action="reschedule",
    )

    assessment = agent.assess(event, recommendation)

    assert assessment.estimated_cost_impact == "$3,000-$5,000"
    assert assessment.recommended_action == "escalate"
    assert "sign-off" in assessment.reasoning.lower()
    agent._gemini.models.generate_content.assert_called_once()