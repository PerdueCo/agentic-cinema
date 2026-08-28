import pytest
import json
from pydantic import TypeAdapter
from unittest.mock import AsyncMock, patch, MagicMock
import src.entry_agent
from src.entry_agent import create_adk_app, root_agent, run_scene42_workflow
from src.shared.schemas import (
    WeatherDisruptionEvent,
    ResearchFinding,
    ScheduleRecommendation,
    BudgetAssessment,
    ProducerRecommendation,
)
from src.orchestrator import Scene42WorkflowResult

@pytest.mark.asyncio
async def test_run_scene42_workflow_awaits_orchestrator_and_serializes_result():
    # Setup
    event_data = {
        "location": {
            "location_id": "loc-1",
            "name": "Set",
            "city": "Atlanta",
            "country": "USA",
            "scene_ids": ["s1"]
        },
        "condition": "storm",
        "scheduled_date": "2026-09-12"
    }

    mock_orchestrator = MagicMock()
    mock_orchestrator.run = AsyncMock()

    # Construct real schema objects
    mock_result = Scene42WorkflowResult(
        event=TypeAdapter(WeatherDisruptionEvent).validate_python(event_data),
        research=ResearchFinding(
            query="Atlanta severe storm",
            summary="Severe weather threatens the exterior production.",
            source_url="https://example.com/weather",
            excerpt="Severe storm warning.",
        ),
        schedule=ScheduleRecommendation(
            affected_scene_ids=["s1"],
            reasoning="Move production to an available stage.",
            suggested_action="relocate",
        ),
        budget=BudgetAssessment(
            estimated_cost_impact="$11,700",
            reasoning="Relocation costs less than a full-day delay.",
            recommended_action="escalate",
        ),
        producer=ProducerRecommendation(
            final_decision="Move Scene 42 to Stage B",
            summary="The exterior production is at risk.",
            rationale="Relocation protects the crew and limits disruption.",
        ),
        requires_human_approval=True
    )
    mock_orchestrator.run.return_value = mock_result

    # Monkeypatch the factory
    with patch("src.entry_agent.create_scene42_orchestrator", return_value=mock_orchestrator):
        result = await run_scene42_workflow(event_data)

    # Assertions
    mock_orchestrator.run.assert_awaited_once()

    # Inspect argument
    args, _ = mock_orchestrator.run.call_args
    assert isinstance(args[0], WeatherDisruptionEvent)

    # Verify result structure and serialization
    assert result["requires_human_approval"] is True
    assert set(result.keys()) == {"event", "research", "schedule", "budget", "producer", "requires_human_approval"}

    # Prove JSON serialization
    serialized = json.dumps(result)
    assert isinstance(serialized, str)

def test_entry_agent_exposes_required_symbols():
    # Assert create_adk_app and root_agent exist
    assert hasattr(src.entry_agent, "create_adk_app")
    assert hasattr(src.entry_agent, "root_agent")

    # Assert STATE is not present
    assert "STATE" not in vars(src.entry_agent)

def test_create_adk_app_is_deferred():
    with patch(
        "src.entry_agent.agent_engines.AdkApp"
    ) as mock_adk_app:
        result = create_adk_app()

    mock_adk_app.assert_called_once_with(agent=root_agent)
    assert result is mock_adk_app.return_value


def test_configure_model_location(monkeypatch):
    monkeypatch.setenv("SCENE42_MODEL_LOCATION", "global")
    monkeypatch.setenv("GOOGLE_CLOUD_LOCATION", "us-central1")

    src.entry_agent.configure_model_location()

    import os
    assert os.environ.get("GOOGLE_CLOUD_LOCATION") == "global"
