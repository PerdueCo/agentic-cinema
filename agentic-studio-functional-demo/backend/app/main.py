from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import json
import os
from typing import Literal
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, TypeAdapter
import vertexai
from vertexai import agent_engines

from src.orchestrator import Scene42WorkflowResult
from src.shared.schemas import SceneLocation, WeatherDisruptionEvent

load_dotenv()

app = FastAPI(title="Agentic Studio Digital Twin API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DecisionRequest(BaseModel):
    decision: Literal["approve", "reject"]
    actor: str = "Executive Producer"
    note: str | None = None

class ResearchRequest(BaseModel):
    objective: str


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

STATE = {
    "scene": {
        "id": "scene-42",
        "name": "Scene 42 — Exterior",
        "location": "Downtown Atlanta",
        "status": "AT_RISK",
        "stage": "Exterior",
    },
    "weather": {
        "rain": "Heavy",
        "wind_mph": 32,
        "lightning_risk": "High",
        "visibility_mi": 2,
        "confidence": 0.92,
    },
    "physics": {
        "wind_load": "HIGH",
        "crane_stability": "MEDIUM",
        "surface_condition": "WET",
        "electrical_exposure": "MEDIUM",
    },
    "safety": {
        "risk": "HIGH",
        "wind_exposure": "HIGH",
        "electrical_hazards": "HIGH",
        "slip_hazard": "HIGH",
        "equipment_risk": "MEDIUM",
        "crew_exposure": "HIGH",
    },
    "recommendation": {
        "action": "MOVE SCENE 42 TO STAGE B",
        "schedule_hours": 2,
        "budget_delta": 11700,
        "resulting_safety_risk": "LOW",
        "reasons": [
            "Severe weather detected",
            "High safety risk outdoors",
            "Stage B available in 2 hours",
            "Lower cost than a full-day delay",
            "Minimal impact to the overall schedule",
        ],
        "explanation": "The recommendation prioritizes crew safety while minimizing schedule and budget disruption.",
    },
    "approval": {
        "id": "approval-scene-42-weather",
        "status": "PENDING",
        "requested_at": now_iso(),
        "actor": None,
        "note": None,
    },
    "digital_twin": {
        "last_updated": None,
        "location": "Exterior",
        "schedule": "UNCHANGED",
        "budget": "UNCHANGED",
        "crew": "UNCHANGED",
        "equipment": "UNCHANGED",
        "safety": "HIGH RISK",
    },
    "events": [],
}


def append_event(kind: str, message: str, payload: dict | None = None):
    event = {
        "id": f"EVT-{datetime.now().strftime('%Y%m%d')}-{str(uuid4())[:8].upper()}",
        "time": now_iso(),
        "kind": kind,
        "message": message,
        "payload": payload or {},
    }
    STATE["events"].insert(0, event)
    del STATE["events"][20:]
    return event


@app.on_event("startup")
def seed_events():
    if not STATE["events"]:
        append_event("weather", "Weather alert updated for Scene 42")
        append_event("scheduling", "Scheduling Agent assessed the Scene 42 production impact")
        append_event("budget", "Budget Agent assessed the cost impact of relocation")
        append_event("approval", "Producer recommendation is awaiting human approval")


@app.get("/api/health")
def health():
    mode = (
        "live"
        if os.getenv("ALLOW_LIVE_AGENTS", "false").lower() == "true"
        else "demo"
    )
    return {
        "status": "ok",
        "mode": mode,
        "gemini_configured": bool(os.getenv("GOOGLE_CLOUD_PROJECT")),
        "parallel_configured": bool(os.getenv("PARALLEL_API_KEY")),
        "agent_engine_configured": bool(
            os.getenv("SCENE42_AGENT_ENGINE_RESOURCE_NAME")
        ),
    }


@app.get("/api/dashboard")
def dashboard():
    return {
        **STATE,
        "kpis": {
            "active_scenes": 18,
            "weather_alerts": 2,
            "pending_approvals": 1 if STATE["approval"]["status"] == "PENDING" else 0,
            "estimated_impact_today": 29400,
            "schedule_impact_hours": 4.2,
            "production_health": 93,
        },
    }


def get_managed_agent_engine():
    """Initialize Vertex AI and retrieve the managed Agent Engine."""
    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project:
        raise ValueError("GOOGLE_CLOUD_PROJECT environment variable is required")
    location = os.getenv("SCENE42_AGENT_ENGINE_LOCATION", "us-central1")
    resource_name = os.getenv("SCENE42_AGENT_ENGINE_RESOURCE_NAME")
    if not resource_name:
        raise ValueError(
            "SCENE42_AGENT_ENGINE_RESOURCE_NAME environment variable is required"
        )

    vertexai.init(project=project, location=location)
    return agent_engines.get(resource_name)


async def run_managed_scene42_workflow(
    event: WeatherDisruptionEvent,
) -> Scene42WorkflowResult:
    """Serialize event, stream via managed engine, and validate output."""
    engine = get_managed_agent_engine()
    serialized_event = json.dumps(asdict(event))
    message = (
        "Please execute the fixed Research, Scheduling, Budget, and Producer "
        "workflow while preserving the human approval boundary for this weather "
        f"disruption event: {serialized_event}"
    )
    user_id = f"user-{uuid4()}"

    def read_field(val, field, default=None):
        if isinstance(val, dict):
            return val.get(field, default)
        return getattr(val, field, default)

    workflow_result_data = None

    async for stream_event in engine.async_stream_query(
        message=message, user_id=user_id
    ):
        # Detect confirmed managed error shapes
        error_code = read_field(stream_event, "error_code")
        if error_code is not None:
            raise RuntimeError(f"Managed error: {error_code}")
        code = read_field(stream_event, "code")
        if code is not None:
            raise RuntimeError(f"Managed error: {code}")

        # Extract content.parts[].function_response.response
        content = read_field(stream_event, "content")
        if content is not None:
            parts = read_field(content, "parts")
            if parts is not None:
                for part in parts:
                    func_resp = read_field(part, "function_response")
                    if func_resp is not None:
                        resp = read_field(func_resp, "response")
                        if resp is not None:
                            workflow_result_data = resp

    if workflow_result_data is None:
        raise RuntimeError(
            "No workflow function response returned from the managed agent engine."
        )

    # Recursively convert any protobuf struct/map containers to plain python dicts
    def to_dict(obj):
        if hasattr(obj, "items"):
            return {k: to_dict(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [to_dict(x) for x in obj]
        return obj

    plain_dict = to_dict(workflow_result_data)
    return TypeAdapter(Scene42WorkflowResult).validate_python(plain_dict)


def build_scene42_event() -> WeatherDisruptionEvent:
    """Create the single fixed disruption event used by this submission."""
    return WeatherDisruptionEvent(
        location=SceneLocation(
            location_id="scene-42-location",
            name="Scene 42 Exterior",
            city="Atlanta",
            country="USA",
            scene_ids=["scene-42"],
        ),
        condition="severe storm",
        scheduled_date="2026-08-29",
        raw_payload={
            "rain": STATE["weather"]["rain"],
            "wind_mph": STATE["weather"]["wind_mph"],
            "lightning_risk": STATE["weather"]["lightning_risk"],
            "visibility_mi": STATE["weather"]["visibility_mi"],
        },
    )


@app.post("/api/scenes/42/analyze")
async def analyze_scene():
    """Run deterministic demo data or the real four-agent workflow."""
    STATE["approval"].update({
        "status": "PENDING",
        "requested_at": now_iso(),
        "actor": None,
        "note": None,
    })
    STATE["scene"]["status"] = "AT_RISK"

    live_enabled = (
        os.getenv("ALLOW_LIVE_AGENTS", "false").lower() == "true"
    )

    if live_enabled:
        missing_keys = [
            name
            for name in ("GOOGLE_CLOUD_PROJECT", "SCENE42_AGENT_ENGINE_RESOURCE_NAME")
            if not os.getenv(name)
        ]
        if missing_keys:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Live agent mode requires configured environment "
                    f"variables: {', '.join(missing_keys)}"
                ),
            )

        try:
            workflow = await run_managed_scene42_workflow(build_scene42_event())
        except Exception as exc:
            append_event(
                "error",
                "Live four-agent workflow failed",
                {"error_type": type(exc).__name__},
            )
            raise HTTPException(
                status_code=502,
                detail=(
                    "The live four-agent workflow could not complete. "
                    f"Error type: {type(exc).__name__}"
                ),
            ) from exc

        STATE["recommendation"].update({
            "action": workflow.producer.final_decision,
            "reasons": [
                workflow.research.summary,
                workflow.schedule.reasoning,
                workflow.budget.reasoning,
            ],
            "explanation": workflow.producer.rationale,
        })

        append_event(
            "analysis",
            "Live Research -> Scheduling -> Budget -> Producer pipeline completed",
            {"mode": "live"},
        )

        return {
            "mode": "live",
            "status": "completed",
            "steps": [
                {
                    "agent": "Research Agent",
                    "status": "complete",
                    "source_url": workflow.research.source_url,
                },
                {
                    "agent": "Scheduling Agent",
                    "status": "complete",
                    "action": workflow.schedule.suggested_action,
                },
                {
                    "agent": "Budget Agent",
                    "status": "complete",
                    "estimated_cost": workflow.budget.estimated_cost_impact,
                },
                {
                    "agent": "Producer Agent",
                    "status": "complete",
                    "requires_human": workflow.requires_human_approval,
                },
            ],
            "evidence": {
                "research": {
                    "summary": workflow.research.summary,
                    "source_url": workflow.research.source_url,
                    "excerpt": workflow.research.excerpt,
                },
                "scheduling": {
                    "action": workflow.schedule.suggested_action,
                    "reasoning": workflow.schedule.reasoning,
                    "affected_scene_ids": (
                        workflow.schedule.affected_scene_ids
                    ),
                },
                "budget": {
                    "estimated_cost": (
                        workflow.budget.estimated_cost_impact
                    ),
                    "action": workflow.budget.recommended_action,
                    "reasoning": workflow.budget.reasoning,
                },
                "producer": {
                    "decision": workflow.producer.final_decision,
                    "summary": workflow.producer.summary,
                    "rationale": workflow.producer.rationale,
                },
            },
            "recommendation": STATE["recommendation"],
            "approval": STATE["approval"],
        }

    append_event(
        "analysis",
        "Demo Research -> Scheduling -> Budget -> Producer pipeline completed",
        {"mode": "demo"},
    )

    return {
        "mode": "demo",
        "status": "completed",
        "steps": [
            {
                "agent": "Research Agent",
                "status": "complete",
                "confidence": 0.92,
            },
            {
                "agent": "Scheduling Agent",
                "status": "complete",
                "action": "RELOCATE",
            },
            {
                "agent": "Budget Agent",
                "status": "complete",
                "estimated_cost": "$11,700",
            },
            {
                "agent": "Producer Agent",
                "status": "complete",
                "requires_human": True,
            },
        ],
        "recommendation": STATE["recommendation"],
        "approval": STATE["approval"],
    }

@app.post("/api/approvals/{approval_id}")
def decide(approval_id: str, request: DecisionRequest):
    if approval_id != STATE["approval"]["id"]:
        raise HTTPException(status_code=404, detail="Approval not found")

    STATE["approval"].update({
        "status": request.decision.upper(),
        "actor": request.actor,
        "note": request.note,
        "decided_at": now_iso(),
    })

    if request.decision == "approve":
        STATE["scene"].update({"status": "MOVED", "stage": "Stage B"})
        STATE["digital_twin"].update({
            "last_updated": now_iso(),
            "location": "Stage B",
            "schedule": "+2 HOURS",
            "budget": "+$11,700",
            "crew": "UPDATED",
            "equipment": "UPDATED",
            "safety": "LOW RISK",
        })
        event = append_event(
            "digital_twin",
            "Human approved recommendation; Scene 42 propagated to Stage B",
            {"decision": "approve", "actor": request.actor},
        )
    else:
        STATE["scene"]["status"] = "PLAN_REJECTED"
        event = append_event(
            "approval",
            "Human rejected recommendation; current production plan retained",
            {"decision": "reject", "actor": request.actor},
        )

    return {"approval": STATE["approval"], "digital_twin": STATE["digital_twin"], "event": event}


@app.post("/api/demo/reset")
def reset_demo():
    STATE["scene"].update({"status": "AT_RISK", "stage": "Exterior"})
    STATE["approval"].update({
        "status": "PENDING",
        "requested_at": now_iso(),
        "actor": None,
        "note": None,
    })
    STATE["digital_twin"].update({
        "last_updated": None,
        "location": "Exterior",
        "schedule": "UNCHANGED",
        "budget": "UNCHANGED",
        "crew": "UNCHANGED",
        "equipment": "UNCHANGED",
        "safety": "HIGH RISK",
    })
    append_event("system", "Demo reset to pending human decision")
    return {"status": "reset"}


@app.post("/api/research")
def research(request: ResearchRequest):
    """Optional live grounded research using Parallel Search.

    Disabled unless ALLOW_LIVE_RESEARCH=true and PARALLEL_API_KEY is set.
    This keeps the demo deterministic and prevents accidental API spend.
    """
    if os.getenv("ALLOW_LIVE_RESEARCH", "false").lower() != "true":
        return {
            "mode": "demo",
            "objective": request.objective,
            "results": [
                {
                    "title": "Demo weather operations source",
                    "url": "https://example.com/weather-operations",
                    "excerpt": "Live Parallel research is disabled. Enable it in .env when you are ready.",
                }
            ],
        }
    if not os.getenv("PARALLEL_API_KEY"):
        raise HTTPException(status_code=400, detail="PARALLEL_API_KEY is not configured")

    from parallel import Parallel

    client = Parallel(api_key=os.environ["PARALLEL_API_KEY"])
    result = client.search(objective=request.objective, search_queries=[request.objective])
    return {
        "mode": "live",
        "objective": request.objective,
        "results": [
            {
                "title": item.title,
                "url": item.url,
                "excerpt": " ".join(item.excerpts[:2]),
            }
            for item in result.results[:5]
        ],
    }
