"""Contract test for the fixed Scene 42 four-agent workflow."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.agents.scheduling_agent import SchedulingAgent
from src.agents.producer_agent import ProducerAgent
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


@pytest.mark.asyncio
async def test_completed_workflow_severe_event_safety_override():
    """Verify that a completed workflow with an authoritative severe event
    never returns 'proceed' in the Producer final decision, and that
    requires_human_approval remains True.
    """
    # 1. Authoritative severe event (e.g., wind_mph >= 30)
    event = WeatherDisruptionEvent(
        location=SceneLocation(
            location_id="scene-42-location",
            name="Scene 42 Exterior",
            city="Atlanta",
            country="USA",
            scene_ids=["scene-42"],
        ),
        condition="windy",
        scheduled_date="2026-08-29",
        raw_payload={"wind_mph": 35},
    )

    # 2. Research finding (favorable)
    finding = ResearchFinding(
        query="Atlanta wind",
        summary="Research suggests local wind gusts might be manageable.",
        source_url="https://example.com/weather",
        excerpt="Wind advisory in Atlanta.",
    )

    # 3. Scheduling Agent with Mock Gemini returning PROCEED
    mock_scheduling_gemini = MagicMock()
    mock_scheduling_gemini.models.generate_content.return_value = SimpleNamespace(
        text="PROCEED\nOptimistic weather assessment: wind is fine."
    )
    scheduling_agent = SchedulingAgent(gemini_client=mock_scheduling_gemini)

    # 4. Budget Agent Mock
    budget = BudgetAssessment(
        estimated_cost_impact="$15,000",
        reasoning="Relocation has standard local staging fees.",
        recommended_action="escalate",
    )
    budget_agent = SimpleNamespace(assess=MagicMock(return_value=budget))

    # 5. Producer Agent with Mock Gemini returning a response containing "proceed"
    mock_producer_gemini = MagicMock()
    mock_producer_gemini.models.generate_content.return_value = SimpleNamespace(
        text="PROCEED\nThe crew can proceed with caution.\nOptimistic summary.\nProceed reasoning."
    )
    producer_agent = ProducerAgent(gemini_client=mock_producer_gemini)

    # 6. Research Agent Mock
    research_agent = SimpleNamespace(investigate=AsyncMock(return_value=finding))

    # 7. Orchestrator
    orchestrator = Scene42Orchestrator(
        research_agent=research_agent,
        scheduling_agent=scheduling_agent,
        budget_agent=budget_agent,
        producer_agent=producer_agent,
    )

    # 8. Run workflow
    result = await orchestrator.run(event)

    # 9. Assertions (specifically including the 3 required assertions)
    assert "proceed" not in result.producer.final_decision.lower()
    assert result.schedule.suggested_action in {"relocate", "reschedule"}
    assert result.requires_human_approval is True

    # Check details of the safety guardrails
    assert result.schedule.suggested_action == "relocate"
    assert result.schedule.reasoning.startswith("Evidence conflict:")
    assert result.producer.final_decision == "Relocate production"


@pytest.mark.asyncio
async def test_completed_workflow_historical_replay_safety_override():
    """Verify that a completed workflow with an authoritative severe event
    never returns 'proceed' in the Producer final decision, and that
    requires_human_approval remains True.
    """
    # 1. Historical scenario estimate; research is mocked below.
    event = WeatherDisruptionEvent(
        location=SceneLocation(
            location_id="scene-42-location",
            name="Scene 42 Exterior",
            city="Atlanta",
            country="USA",
            scene_ids=["scene-42"],
        ),
        condition="Downtown Atlanta EF2 tornado",
        scheduled_date="2008-03-14",
        evidence_mode="historical_replay",
        raw_payload={"wind_mph": 130},
    )

    # 2. Research finding (favorable)
    finding = ResearchFinding(
        query="Atlanta wind",
        summary="Research suggests local wind gusts might be manageable.",
        source_url="https://example.com/weather",
        excerpt="Wind advisory in Atlanta.",
    )

    # 3. Scheduling Agent with Mock Gemini returning PROCEED
    mock_scheduling_gemini = MagicMock()
    mock_scheduling_gemini.models.generate_content.return_value = SimpleNamespace(
        text="PROCEED\nOptimistic weather assessment: wind is fine."
    )
    scheduling_agent = SchedulingAgent(gemini_client=mock_scheduling_gemini)

    # 4. Budget Agent Mock
    budget = BudgetAssessment(
        estimated_cost_impact="$15,000",
        reasoning="Relocation has standard local staging fees.",
        recommended_action="escalate",
    )
    budget_agent = SimpleNamespace(assess=MagicMock(return_value=budget))

    # 5. Producer Agent with Mock Gemini returning a response containing "proceed"
    mock_producer_gemini = MagicMock()
    mock_producer_gemini.models.generate_content.return_value = SimpleNamespace(
        text="PROCEED\nThe crew can proceed with caution.\nOptimistic summary.\nProceed reasoning."
    )
    producer_agent = ProducerAgent(gemini_client=mock_producer_gemini)

    # 6. Research Agent Mock
    research_agent = SimpleNamespace(investigate=AsyncMock(return_value=finding))

    # 7. Orchestrator
    orchestrator = Scene42Orchestrator(
        research_agent=research_agent,
        scheduling_agent=scheduling_agent,
        budget_agent=budget_agent,
        producer_agent=producer_agent,
    )

    # 8. Run workflow
    result = await orchestrator.run(event)

    # 9. Assertions (specifically including the 3 required assertions)
    assert "proceed" not in result.producer.final_decision.lower()
    assert result.schedule.suggested_action in {"relocate", "reschedule"}
    assert result.requires_human_approval is True

    # Check details of the safety guardrails
    assert result.schedule.suggested_action == "relocate"
    assert result.schedule.reasoning.startswith("Evidence conflict:")
    assert result.producer.final_decision == "Relocate production"
