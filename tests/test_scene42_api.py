"""API contract tests for Scene 42 and the human decision boundary."""

from __future__ import annotations

import sys
from copy import deepcopy
from unittest.mock import AsyncMock, patch

import pytest
from pathlib import Path

from fastapi.testclient import TestClient

BACKEND_DIRECTORY = (
    Path(__file__).resolve().parents[1]
    / "agentic-studio-functional-demo"
    / "backend"
)
sys.path.insert(0, str(BACKEND_DIRECTORY))

from app.main import app  # noqa: E402
import app.main as backend  # noqa: E402
from src.orchestrator import Scene42WorkflowResult  # noqa: E402
from src.shared.schemas import (  # noqa: E402
    BudgetAssessment, ProducerRecommendation, ResearchFinding, ScheduleRecommendation,
)


def test_scene42_analysis_uses_fixed_four_agent_scope_and_waits_for_human():
    with TestClient(app) as client:
        client.post("/api/demo/reset")

        response = client.post("/api/scenes/42/analyze")

        assert response.status_code == 200
        body = response.json()

        assert [step["agent"] for step in body["steps"]] == [
            "Research Agent",
            "Scheduling Agent",
            "Budget Agent",
            "Producer Agent",
        ]
        assert body["approval"]["status"] == "PENDING"

        dashboard = client.get("/api/dashboard").json()
        assert dashboard["scene"]["stage"] == "Exterior"
        assert dashboard["digital_twin"]["location"] == "Exterior"
        assert dashboard["digital_twin"]["schedule"] == "UNCHANGED"
        assert dashboard["digital_twin"]["budget"] == "UNCHANGED"
        assert dashboard["digital_twin"]["safety"] == "HIGH RISK"


def test_human_approval_propagates_recommendation_to_digital_twin():
    with TestClient(app) as client:
        client.post("/api/demo/reset")
        client.post("/api/scenes/42/analyze")

        response = client.post(
            "/api/approvals/approval-scene-42-weather",
            json={
                "decision": "approve",
                "actor": "Executive Producer",
                "note": "Approved after reviewing the four-agent evidence.",
            },
        )

        assert response.status_code == 200
        body = response.json()

        assert body["approval"]["status"] == "APPROVE"
        assert body["digital_twin"]["location"] == "Stage B"
        assert body["digital_twin"]["schedule"] == "+2 HOURS"
        assert body["digital_twin"]["budget"] == "+$11,700"
        assert body["digital_twin"]["safety"] == "LOW RISK"


@pytest.fixture(autouse=True)
def isolate_scene42_api(monkeypatch):
    """Existing tests are demo-only; never inherit live mode from local .env."""
    snapshot = deepcopy(backend.STATE)
    monkeypatch.setenv("ALLOW_LIVE_AGENTS", "false")
    monkeypatch.delenv("PARALLEL_API_KEY", raising=False)
    with patch("app.main.get_managed_agent_engine",
               side_effect=AssertionError("External engine access forbidden in API tests")):
        try:
            yield
        finally:
            backend.STATE.clear()
            backend.STATE.update(snapshot)


def test_live_analysis_sends_historical_event_and_preserves_human_boundary(monkeypatch):
    monkeypatch.setenv("ALLOW_LIVE_AGENTS", "true")
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-project")
    monkeypatch.setenv("SCENE42_AGENT_ENGINE_RESOURCE_NAME", "test-engine")
    event = backend.build_scene42_event()
    workflow = Scene42WorkflowResult(
        event=event,
        research=ResearchFinding(
            query="Atlanta 2008-03-14 tornado",
            summary="Historical candidate evidence; human review required.",
            source_url="https://example.com/live-result",
            excerpt="On March 14, 2008 a tornado struck Atlanta.",
        ),
        schedule=ScheduleRecommendation(["scene-42"], "Severe scenario wind", "reschedule"),
        budget=BudgetAssessment("Demonstration estimate", "Simulation only", "escalate"),
        producer=ProducerRecommendation("Reschedule production", "Simulation", "Human review"),
        requires_human_approval=True,
    )
    with patch("app.main.run_managed_scene42_workflow", new_callable=AsyncMock,
               return_value=workflow) as managed:
        with TestClient(app) as client:
            client.post("/api/demo/reset")
            before = client.get("/api/dashboard").json()["digital_twin"]
            response = client.post("/api/scenes/42/analyze")
            after = client.get("/api/dashboard").json()["digital_twin"]
    assert response.status_code == 200
    managed.assert_awaited_once()
    sent = managed.await_args.args[0]
    assert sent.evidence_mode == "historical_replay"
    assert sent.scheduled_date == "2008-03-14"
    assert sent.location.city == "Atlanta" and sent.location.country == "USA"
    assert sent.condition == "Downtown Atlanta EF2 tornado"
    assert sent.raw_payload["wind_mph"] == 130
    assert sent.raw_payload["historical_metadata"] == backend.SCENE42_HISTORICAL_METADATA
    assert not {"rain", "lightning_risk", "visibility_mi", "confidence"} & sent.raw_payload.keys()
    body = response.json()
    assert body["scenario"]["evidence_mode"] == "historical_replay"
    assert body["scenario"]["production_is_simulated"] is True
    assert body["evidence"]["research"]["source_url"] == "https://example.com/live-result"
    assert body["evidence"]["research"]["retrieved_at"]
    assert body["steps"][3]["requires_human"] is True
    assert body["approval"]["status"] == "PENDING"
    assert after == before


def test_historical_builder_does_not_share_mutable_metadata():
    first = backend.build_scene42_event()
    first.raw_payload["historical_metadata"]["reference_urls"].clear()
    assert backend.build_scene42_event().raw_payload["historical_metadata"]["reference_urls"]
