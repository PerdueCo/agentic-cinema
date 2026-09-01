"""API contract tests for Scene 42 and the human decision boundary."""

from __future__ import annotations

import sys
import asyncio
from copy import deepcopy
from dataclasses import replace
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


def test_demo_approval_records_relocation_without_inventing_assignments():
    with TestClient(app) as client:
        client.post("/api/demo/reset")
        analysis = client.post("/api/scenes/42/analyze").json()
        before = client.get("/api/dashboard").json()["digital_twin"]

        response = client.post(
            f"/api/approvals/{analysis['approval']['id']}",
            json={
                "decision": "approve",
                "actor": "Executive Producer",
                "note": "Approved after reviewing the four-agent evidence.",
            },
        )

        assert response.status_code == 200
        body = response.json()

        assert body["approval"]["status"] == "APPROVE"
        for field in ("location", "schedule", "budget", "crew", "equipment", "safety"):
            assert body["digital_twin"][field] == before[field]
        assert "destination pending" in body["digital_twin"]["decision_status"]
        assert body["event"]["payload"]["approved_plan"]["mode"] == "demo"
        assert body["event"]["payload"]["approved_plan"]["estimate_only"] is True


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


@pytest.fixture
def live_approval_workflow(monkeypatch):
    monkeypatch.setenv("ALLOW_LIVE_AGENTS", "true")
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-project")
    monkeypatch.setenv("SCENE42_AGENT_ENGINE_RESOURCE_NAME", "test-engine")
    return Scene42WorkflowResult(
        event=backend.build_scene42_event(),
        research=ResearchFinding("Historical replay", "Historical candidate", "https://example.com", "Evidence"),
        schedule=ScheduleRecommendation(["scene-42"], "Severe weather scenario", "reschedule"),
        budget=BudgetAssessment("$15,000 - $45,000", "Estimate only", "escalate"),
        producer=ProducerRecommendation("Reschedule production", "Simulation summary", "Human review"),
        requires_human_approval=True,
    )


def submit_decision(client, approval_id, decision="approve"):
    return client.post(
        f"/api/approvals/{approval_id}",
        json={"decision": decision, "actor": "Test Producer", "note": "Reviewed simulation"},
    )


@pytest.mark.parametrize("action,scene_status", [
    ("reschedule", "RESCHEDULE_REQUIRED"),
    ("relocate", "RELOCATION_REQUIRED"),
    ("proceed", "PLAN_APPROVED"),
])
def test_live_approval_applies_only_structured_action(live_approval_workflow, action, scene_status):
    workflow = live_approval_workflow
    workflow.schedule.suggested_action = action
    # Free text must not be parsed as a destination, time, or cost instruction.
    workflow.producer.final_decision = "Move to Stage B in 2 hours for $11,700"
    with patch("app.main.run_managed_scene42_workflow", new_callable=AsyncMock, return_value=workflow):
        with TestClient(app) as client:
            client.post("/api/demo/reset")
            backend.STATE["digital_twin"].update({
                "location": "Original location", "budget": "Existing budget",
                "crew": "Original crew", "equipment": "Original equipment",
                "safety": "HIGH RISK",
            })
            before = client.get("/api/dashboard").json()
            response = client.post("/api/scenes/42/analyze")
            assert response.status_code == 200
            analysis = response.json()
            assert client.get("/api/dashboard").json()["digital_twin"] == before["digital_twin"]
            assert analysis["recommendation"]["budget_delta"] is None
            assert analysis["recommendation"]["schedule_hours"] is None
            assert analysis["recommendation"]["estimate_only"] is True

            decision = submit_decision(client, analysis["approval"]["id"])
            assert decision.status_code == 200
            body = decision.json()
            twin = body["digital_twin"]
            for field in ("location", "budget", "crew", "equipment", "safety"):
                assert twin[field] == before["digital_twin"][field]
            if action == "reschedule":
                assert twin["schedule"] == "Rescheduling approved — date pending"
            else:
                assert twin["schedule"] == before["digital_twin"]["schedule"]
            if action == "relocate":
                assert "destination pending" in twin["decision_status"]
            assert twin["last_updated"] is not None
            assert client.get("/api/dashboard").json()["scene"]["status"] == scene_status
            assert client.get("/api/dashboard").json()["scene"]["stage"] == before["scene"]["stage"]
            plan = body["event"]["payload"]["approved_plan"]
            assert plan["schedule_action"] == action
            assert plan["estimated_cost"] == "$15,000 - $45,000"
            assert plan["producer_summary"] == workflow.producer.summary
            assert plan["rationale"] == workflow.producer.rationale
            assert plan["requires_human_approval"] is True
            assert body["event"]["payload"]["actor"] == "Test Producer"
            assert body["event"]["payload"]["decided_at"] == body["approval"]["decided_at"]
            assert backend.STATE["pending_plan"] is None


def test_rejection_preserves_entire_twin_and_scene(live_approval_workflow):
    with patch("app.main.run_managed_scene42_workflow", new_callable=AsyncMock, return_value=live_approval_workflow):
        with TestClient(app) as client:
            client.post("/api/demo/reset")
            analysis = client.post("/api/scenes/42/analyze").json()
            before = client.get("/api/dashboard").json()
            response = submit_decision(client, analysis["approval"]["id"], "reject")
            assert response.status_code == 200
            after = client.get("/api/dashboard").json()
            assert after["digital_twin"] == before["digital_twin"]
            assert after["scene"] == before["scene"]
            assert after["approval"]["status"] == "REJECT"
            assert response.json()["event"]["payload"]["rejected_plan"]["schedule_action"] == "reschedule"


@pytest.mark.parametrize("first_decision", ["approve", "reject"])
def test_duplicate_decisions_are_rejected_without_second_update(first_decision):
    with TestClient(app) as client:
        client.post("/api/demo/reset")
        analysis = client.post("/api/scenes/42/analyze").json()
        approval_id = analysis["approval"]["id"]
        assert submit_decision(client, approval_id, first_decision).status_code == 200
        before = client.get("/api/dashboard").json()
        assert submit_decision(client, approval_id).status_code == 409
        assert client.get("/api/dashboard").json() == before


def test_no_analysis_and_reset_invalidate_approval():
    with TestClient(app) as client:
        client.post("/api/demo/reset")
        initial = client.get("/api/dashboard").json()
        assert initial["approval"]["status"] == "AWAITING_ANALYSIS"
        assert initial["kpis"]["pending_approvals"] == 0
        assert submit_decision(client, initial["approval"]["id"]).status_code == 409
        analysis = client.post("/api/scenes/42/analyze").json()
        assert submit_decision(client, analysis["approval"]["id"]).status_code == 200
        client.post("/api/demo/reset")
        reset = client.get("/api/dashboard").json()
        assert reset["pending_plan"] is None
        assert reset["approval"]["decided_at"] is None
        assert reset["recommendation"]["action"] == "Analysis required"
        assert reset["recommendation"]["reasons"] == []
        assert reset["digital_twin"] == backend.INITIAL_TWIN
        assert submit_decision(client, analysis["approval"]["id"]).status_code == 409


def test_new_analysis_rejects_old_approval_id():
    with TestClient(app) as client:
        client.post("/api/demo/reset")
        first = client.post("/api/scenes/42/analyze").json()
        second = client.post("/api/scenes/42/analyze").json()
        assert first["approval"]["id"] != second["approval"]["id"]
        before = client.get("/api/dashboard").json()
        assert submit_decision(client, first["approval"]["id"]).status_code == 409
        assert client.get("/api/dashboard").json() == before
        assert submit_decision(client, second["approval"]["id"]).status_code == 200


@pytest.mark.parametrize("problem", ["exception", "action", "human", "configuration"])
def test_failed_analysis_cannot_leave_old_plan_approvable(live_approval_workflow, monkeypatch, problem):
    workflow = live_approval_workflow
    with patch("app.main.run_managed_scene42_workflow", new_callable=AsyncMock, return_value=workflow) as managed:
        with TestClient(app) as client:
            client.post("/api/demo/reset")
            first = client.post("/api/scenes/42/analyze").json()
            before = client.get("/api/dashboard").json()["digital_twin"]
            if problem == "exception":
                managed.side_effect = RuntimeError("Private internal details")
            elif problem == "action":
                workflow.schedule.suggested_action = "unsupported"
            elif problem == "human":
                managed.return_value = replace(workflow, requires_human_approval=False)
            else:
                monkeypatch.delenv("GOOGLE_CLOUD_PROJECT")
            response = client.post("/api/scenes/42/analyze")
            assert response.status_code == (400 if problem == "configuration" else 502)
            assert "Private internal details" not in response.text
            after = client.get("/api/dashboard").json()
            assert after["approval"]["status"] == "ERROR"
            assert after["pending_plan"] is None
            assert after["digital_twin"] == before
            assert after["kpis"]["pending_approvals"] == 0
            assert submit_decision(client, first["approval"]["id"]).status_code == 409


@pytest.mark.asyncio
@pytest.mark.parametrize("replacement", ["reset", "newer_analysis"])
@pytest.mark.parametrize("old_fails", [False, True])
async def test_late_analysis_cannot_restore_invalidated_plan(
    live_approval_workflow, replacement, old_fails
):
    started = asyncio.Event()
    release = asyncio.Event()
    calls = 0

    async def controlled_workflow(event):
        nonlocal calls
        calls += 1
        if calls == 1:
            started.set()
            await release.wait()
            if old_fails:
                raise RuntimeError("Old request failed")
        return live_approval_workflow

    with patch("app.main.run_managed_scene42_workflow", side_effect=controlled_workflow):
        task = asyncio.create_task(backend.analyze_scene())
        try:
            await asyncio.wait_for(started.wait(), timeout=2)
            in_progress_id = backend.STATE["approval"]["id"]
            with pytest.raises(backend.HTTPException) as blocked:
                backend.decide(in_progress_id, backend.DecisionRequest(decision="approve"))
            assert blocked.value.status_code == 409
            if replacement == "reset":
                backend.reset_demo()
            else:
                await backend.analyze_scene()
            snapshot = deepcopy(backend.STATE)
            release.set()
            with pytest.raises(backend.HTTPException) as stale:
                await asyncio.wait_for(task, timeout=2)
            assert stale.value.status_code == (502 if old_fails else 409)
            assert backend.STATE == snapshot
        finally:
            release.set()
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
