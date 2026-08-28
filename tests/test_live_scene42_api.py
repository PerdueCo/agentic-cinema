"""FastAPI contract test for live four-agent orchestration."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

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

    workflow_result = SimpleNamespace(
        research=finding,
        schedule=schedule,
        budget=budget,
        producer=producer,
        requires_human_approval=True,
    )
    fake_orchestrator = SimpleNamespace(
        run=AsyncMock(return_value=workflow_result)
    )

    monkeypatch.setenv("ALLOW_LIVE_AGENTS", "true")
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-gcp-project")
    monkeypatch.setenv("PARALLEL_API_KEY", "test-parallel-key")
    monkeypatch.setattr(
        main_module,
        "build_live_orchestrator",
        lambda: fake_orchestrator,
        raising=False,
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

    fake_orchestrator.run.assert_awaited_once()
