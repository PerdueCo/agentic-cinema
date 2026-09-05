"""FastAPI contract test for live four-agent orchestration."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
import sys

import pytest

from fastapi.testclient import TestClient

from src.orchestrator import Scene42WorkflowResult
from src.shared.schemas import (
    BudgetAssessment,
    ProducerRecommendation,
    ResearchFinding,
    ScheduleRecommendation,
)

BACKEND_DIRECTORY = (
    Path(__file__).resolve().parents[1]
    / "agentic-studio-functional-demo"
    / "backend"
)
sys.path.insert(0, str(BACKEND_DIRECTORY))

import app.main as main_module  # noqa: E402


@pytest.fixture(autouse=True)
def restore_shared_state():
    with main_module.STATE_LOCK:
        snapshot = deepcopy(main_module.STATE)
    try:
        yield
    finally:
        with main_module.STATE_LOCK:
            main_module.STATE.clear()
            main_module.STATE.update(snapshot)


def test_live_mode_calls_orchestrator_and_preserves_human_boundary(
    monkeypatch,
):
    finding = ResearchFinding(
        query="Scene 42 Atlanta weather",
        summary="A severe storm threatens the exterior scene.",
        source_url="https://example.com/weather",
        excerpt="Severe storm warning.",
    )
    schedule = ScheduleRecommendation(
        affected_scene_ids=["scene-42"],
        reasoning="Move the exterior production to Stage B.",
        suggested_action="relocate",
    )
    budget = BudgetAssessment(
        estimated_cost_impact="$11,700",
        reasoning="Relocation costs less than a full-day delay.",
        recommended_action="escalate",
    )
    producer = ProducerRecommendation(
        final_decision="Move Scene 42 to Stage B",
        summary="Severe weather makes the exterior setup unsafe.",
        rationale="Relocation protects the crew and limits disruption.",
    )

    workflow_result = Scene42WorkflowResult(
        event=main_module.build_scene42_event(),
        research=finding,
        schedule=schedule,
        budget=budget,
        producer=producer,
        requires_human_approval=True,
    )
    workflow_result_dict = asdict(workflow_result)

    monkeypatch.setenv("ALLOW_LIVE_AGENTS", "true")
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-gcp-project")
    monkeypatch.setenv("SCENE42_AGENT_ENGINE_LOCATION", "us-central1")
    monkeypatch.setenv(
        "SCENE42_AGENT_ENGINE_RESOURCE_NAME",
        "projects/test-project/locations/us-central1/reasoningEngines/fake-engine",
    )
    monkeypatch.delenv("PARALLEL_API_KEY", raising=False)

    class FakeManagedEngine:
        def __init__(self):
            self.calls = []

        async def async_stream_query(self, message, user_id):
            self.calls.append((message, user_id))
            yield {
                "content": {
                    "parts": [
                        {
                            "function_response": {
                                "response": workflow_result_dict
                            }
                        }
                    ]
                }
            }

    fake_engine = FakeManagedEngine()
    monkeypatch.setattr(
        main_module,
        "get_managed_agent_engine",
        lambda: fake_engine,
    )

    with TestClient(main_module.app) as client:
        client.post("/api/demo/reset")
        response = client.post("/api/scenes/42/analyze")

        assert response.status_code == 200
        body = response.json()

        assert body["mode"] == "live"
        assert [step["agent"] for step in body["steps"]] == [
            "Research Agent",
            "Scheduling Agent",
            "Budget Agent",
            "Producer Agent",
        ]
        assert body["steps"][3]["requires_human"] is True
        assert body["evidence"]["research"]["source_url"] == (
            "https://example.com/weather"
        )
        assert body["evidence"]["scheduling"]["action"] == "relocate"
        assert body["evidence"]["budget"]["estimated_cost"] == "$11,700"
        assert body["recommendation"]["action"] == (
            "Move Scene 42 to Stage B"
        )
        assert body["approval"]["status"] == "PENDING"

        dashboard = client.get("/api/dashboard").json()
        assert dashboard["scene"]["stage"] == "Exterior"
        assert dashboard["digital_twin"]["location"] == "Exterior"
        assert dashboard["approval"]["id"] == body["approval"]["id"]
        assert dashboard["pending_plan"]["schedule_action"] == "relocate"
        before = dashboard["digital_twin"]

        # Free-text "Stage B" is not a structured, confirmed destination.
        decision = client.post(
            f"/api/approvals/{body['approval']['id']}",
            json={"decision": "approve", "actor": "Test Producer"},
        )
        assert decision.status_code == 200
        twin = decision.json()["digital_twin"]
        for field in ("location", "schedule", "budget", "crew", "equipment", "safety"):
            assert twin[field] == before[field]
        assert "destination pending" in twin["decision_status"]
        assert decision.json()["event"]["payload"]["approved_plan"]["estimated_cost"] == "$11,700"

    assert len(fake_engine.calls) == 1
    query_message, query_user_id = fake_engine.calls[0]
    assert "Atlanta" in query_message
    assert "scene-42" in query_message
    assert query_user_id.startswith("user-")


@pytest.mark.parametrize("stream_event,category", [
    ({"error_code": "PRIVATE_SERVICE_DETAIL"}, "managed_error_event"),
    ({"content": {"parts": []}}, "missing_function_response"),
])
def test_managed_stream_failure_is_correlated_without_leaking_payload(monkeypatch, caplog, stream_event, category):
    monkeypatch.setenv("ALLOW_LIVE_AGENTS", "true")
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-project")
    monkeypatch.setenv("SCENE42_AGENT_ENGINE_RESOURCE_NAME", "test-engine")

    class BrokenEngine:
        async def async_stream_query(self, **kwargs):
            yield stream_event

    monkeypatch.setattr(main_module, "get_managed_agent_engine", lambda: BrokenEngine())
    with TestClient(main_module.app) as client:
        client.post("/api/demo/reset")
        response = client.post("/api/scenes/42/analyze")
        assert response.status_code == 502
        reference = response.json()["detail"]["support_reference"]
        body = client.get("/api/dashboard").json()
        assert body["attempt"]["reference"] == reference
        assert body["attempt"]["category"] == category
        assert body["attempt"]["stage"] == "managed_stream"
        assert body["approval"]["status"] == "ERROR"
        assert body["analysis"] is None
        assert "PRIVATE_SERVICE_DETAIL" not in response.text + caplog.text
