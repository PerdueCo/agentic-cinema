"""API contract tests for Scene 42 and the human decision boundary."""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient

BACKEND_DIRECTORY = (
    Path(__file__).resolve().parents[1]
    / "agentic-studio-functional-demo"
    / "backend"
)
sys.path.insert(0, str(BACKEND_DIRECTORY))

from app.main import app  # noqa: E402


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
