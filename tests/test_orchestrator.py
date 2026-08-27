"""Contract test for the fixed Scene 42 four-agent workflow."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.orchestrator import Scene42Orchestrator
from src.shared.schemas import (
    BudgetAssessment,
    ProducerRecommendation,
    ResearchFinding,
    ScheduleRecommendation,
    SceneLocation,
    WeatherDisruptionEvent,
)


@pytest.mark.asyncio
async def test_scene42_orchestrator_runs_four_agents_in_order():
    event = WeatherDisruptionEvent(
        location=SceneLocation(
            location_id="scene-42-location",
            name="Scene 42 Exterior",
            city="Atlanta",
            country="USA",
            scene_ids=["scene-42"],
        ),
        condition="severe storm",
        scheduled_date="2026-08-29",
    )

    finding = ResearchFinding(
        query="Atlanta severe storm",
        summary="Severe weather threatens the exterior production.",
        source_url="https://example.com/weather",
        excerpt="Severe storm warning.",
    )
    schedule = ScheduleRecommendation(
        affected_scene_ids=["scene-42"],
        reasoning="Outdoor production should move to an available stage.",
        suggested_action="relocate",
    )
    budget = BudgetAssessment(
        estimated_cost_impact="$10,000-$12,000",
        reasoning="Relocation is less expensive than a full-day delay.",
        recommended_action="escalate",
    )
    producer = ProducerRecommendation(
        final_decision="Move Scene 42 to Stage B",
        summary="The exterior scene is at risk from severe weather.",
        rationale="Relocation protects the crew and limits disruption.",
    )

    research_agent = SimpleNamespace(investigate=AsyncMock(return_value=finding))
    scheduling_agent = SimpleNamespace(recommend=MagicMock(return_value=schedule))
    budget_agent = SimpleNamespace(assess=MagicMock(return_value=budget))
    producer_agent = SimpleNamespace(recommend=MagicMock(return_value=producer))

    orchestrator = Scene42Orchestrator(
        research_agent=research_agent,
        scheduling_agent=scheduling_agent,
        budget_agent=budget_agent,
        producer_agent=producer_agent,
    )

    result = await orchestrator.run(event)

    assert result.event is event
    assert result.research is finding
    assert result.schedule is schedule
    assert result.budget is budget
    assert result.producer is producer
    assert result.requires_human_approval is True

    research_agent.investigate.assert_awaited_once_with(event)
    scheduling_agent.recommend.assert_called_once_with(event, finding)
    budget_agent.assess.assert_called_once_with(event, schedule)
    producer_agent.recommend.assert_called_once_with(
        event, finding, schedule, budget
    )
