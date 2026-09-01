from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timezone
import json
import os
from typing import Literal
from threading import RLock
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
        "action": "Analysis required",
        "schedule_hours": None,
        "budget_delta": None,
        "resulting_safety_risk": "Human review required",
        "reasons": [],
        "explanation": "Run analysis before requesting a human decision.",
    },
    "approval": {
        "id": None,
        "status": "AWAITING_ANALYSIS",
        "requested_at": None,
        "actor": None,
        "note": None,
    },
    "digital_twin": {
        "last_updated": None,
        "decision_status": "Awaiting analysis and human approval",
        "location": "Exterior",
        "schedule": "UNCHANGED",
        "budget": "UNCHANGED",
        "crew": "UNCHANGED",
        "equipment": "UNCHANGED",
        "safety": "HIGH RISK",
    },
    "events": [],
}

# State is local to ONE process. Multiple workers require a shared transactional store.
STATE_LOCK = RLock()
INITIAL_SCENE = deepcopy(STATE["scene"])
INITIAL_TWIN = deepcopy(STATE["digital_twin"])
STATE["pending_plan"] = None


def clear_pending(status: str) -> str:
    """Caller holds STATE_LOCK. Rotate the ID to invalidate older requests."""
    approval_id = f"approval-scene-42-{uuid4()}"
    STATE["approval"] = {
        "id": approval_id,
        "status": status,
        "requested_at": now_iso() if status == "ANALYZING" else None,
        "actor": None,
        "note": None,
        "decided_at": None,
    }
    STATE["pending_plan"] = None
    STATE["recommendation"] = {
        "action": "Analysis in progress" if status == "ANALYZING" else "Analysis required",
        "schedule_hours": None,
        "budget_delta": None,
        "resulting_safety_risk": "Human review required",
        "reasons": [],
        "explanation": "Run analysis before requesting a human decision.",
    }
    return approval_id


def fail_analysis(approval_id: str) -> None:
    with STATE_LOCK:
        if STATE["approval"]["id"] == approval_id:
            clear_pending("ERROR")
            STATE["recommendation"]["action"] = "Analysis failed — retry required"
            append_event("error", "Analysis failed; no recommendation is available for approval")


def publish_plan(approval_id: str, plan: dict) -> dict:
    """Publish only the current analysis; never change the Digital Twin."""
    if plan["schedule_action"] not in {"proceed", "relocate", "reschedule"}:
        raise ValueError("Unsupported scheduling action")
    if plan["requires_human_approval"] is not True:
        raise ValueError("Human approval must be required")
    with STATE_LOCK:
        if (
            STATE["approval"]["id"] != approval_id
            or STATE["approval"]["status"] != "ANALYZING"
        ):
            raise HTTPException(status_code=409, detail="Analysis superseded or reset.")
        STATE["pending_plan"] = deepcopy({"approval_id": approval_id, **plan})
        STATE["recommendation"] = {
            "action": plan["producer_decision"],
            "schedule_action": plan["schedule_action"],
            "estimated_cost": plan["estimated_cost"],
            "estimate_only": True,
            "schedule_hours": None,
            "budget_delta": None,
            "resulting_safety_risk": "Human review required",
            "reasons": list(plan["reasons"]),
            "explanation": plan["rationale"],
        }
        STATE["approval"]["status"] = "PENDING"
        STATE["approval"]["requested_at"] = now_iso()
        append_event(
            "analysis",
            "Research -> Scheduling -> Budget -> Producer recommendation awaits human approval",
            {"mode": plan["mode"], "approval_id": approval_id,
             "schedule_action": plan["schedule_action"]},
        )
        return deepcopy({
            "recommendation": STATE["recommendation"],
            "approval": STATE["approval"],
        })


def append_event(kind: str, message: str, payload: dict | None = None):
    with STATE_LOCK:
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
        append_event("approval", "Run analysis before requesting human approval")


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
    with STATE_LOCK:
        return deepcopy({
            **STATE,
            "kpis": {
                "active_scenes": 18,
                "weather_alerts": 2,
                "pending_approvals": 1 if STATE["approval"]["status"] == "PENDING" else 0,
                "estimated_impact_today": 29400,
                "schedule_impact_hours": 4.2,
                "production_health": 93,
            },
        })


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


# Historical event inputs for a FICTIONAL production replay, not set measurements.
# Reference URLs identify the intended event; they are not runtime search results.
SCENE42_HISTORICAL_METADATA = {
    "event_date": "2008-03-14",
    "event_time_local": "9:38 PM",
    "area": "Downtown Atlanta",
    "city": "Atlanta",
    "state": "Georgia",
    "country": "USA",
    "tornado_rating": "EF2",
    "estimated_max_wind_mph": 130,
    "reference_urls": [
        "https://www.weather.gov/ffc/atltor31408",
        "https://www.weather.gov/ffc/pns32308.txt",
    ],
}


def build_scene42_event() -> WeatherDisruptionEvent:
    """Build the fixed historical event for a fictional Scene 42 production."""
    metadata = deepcopy(SCENE42_HISTORICAL_METADATA)
    return WeatherDisruptionEvent(
        location=SceneLocation(
            location_id="scene-42-location",
            name="Scene 42 Exterior",
            city=metadata["city"],
            country=metadata["country"],
            scene_ids=["scene-42"],
        ),
        condition=f"{metadata['area']} {metadata['tornado_rating']} tornado",
        scheduled_date=metadata["event_date"],
        evidence_mode="historical_replay",
        raw_payload={
            "wind_mph": metadata["estimated_max_wind_mph"],
            "historical_metadata": metadata,
        },
    )


@app.post("/api/scenes/42/analyze")
async def analyze_scene():
    """Run deterministic demo data or the real four-agent workflow."""
    with STATE_LOCK:
        approval_id = clear_pending("ANALYZING")

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
            fail_analysis(approval_id)
            raise HTTPException(
                status_code=400,
                detail=(
                    "Live agent mode requires configured environment "
                    f"variables: {', '.join(missing_keys)}"
                ),
            )

        try:
            event = build_scene42_event()
            workflow = await run_managed_scene42_workflow(event)
            snapshot = publish_plan(approval_id, {
                "mode": "live",
                "schedule_action": workflow.schedule.suggested_action,
                "producer_decision": workflow.producer.final_decision,
                "producer_summary": workflow.producer.summary,
                "rationale": workflow.producer.rationale,
                "estimated_cost": workflow.budget.estimated_cost_impact,
                "estimate_only": True,
                "requires_human_approval": workflow.requires_human_approval,
                "reasons": [
                    workflow.research.summary,
                    workflow.schedule.reasoning,
                    workflow.budget.reasoning,
                ],
            })
        except HTTPException:
            fail_analysis(approval_id)
            raise
        except Exception as exc:
            fail_analysis(approval_id)
            raise HTTPException(
                status_code=502,
                detail=(
                    "The live four-agent workflow could not complete. "
                    f"Error type: {type(exc).__name__}"
                ),
            ) from exc

        return {
            "mode": "live",
            "status": "completed",
            "scenario": {
                "evidence_mode": event.evidence_mode,
                "production_is_simulated": True,
                "event_date": event.scheduled_date,
                "historical_metadata": event.raw_payload["historical_metadata"],
            },
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
                    "query": workflow.research.query,
                    "retrieved_at": workflow.research.retrieved_at.isoformat(),
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
            "recommendation": snapshot["recommendation"],
            "approval": snapshot["approval"],
        }

    # Demonstration estimate, not a booked destination or committed expenditure.
    snapshot = publish_plan(approval_id, {
        "mode": "demo",
        "schedule_action": "relocate",
        "producer_decision": "Relocation recommended — destination pending",
        "producer_summary": "Demonstration weather disruption affects exterior filming.",
        "rationale": "Approval authorizes planning; assignments remain unconfirmed.",
        "estimated_cost": "$11,700 (demo estimate; not committed)",
        "estimate_only": True,
        "requires_human_approval": True,
        "reasons": [
            "Demonstration weather disruption",
            "Relocation requires destination confirmation",
            "Budget is an estimate, not an approved expenditure",
        ],
    })

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
                "estimated_cost": snapshot["recommendation"]["estimated_cost"],
            },
            {
                "agent": "Producer Agent",
                "status": "complete",
                "requires_human": True,
            },
        ],
        "recommendation": snapshot["recommendation"],
        "approval": snapshot["approval"],
    }

@app.post("/api/approvals/{approval_id}")
def decide(approval_id: str, request: DecisionRequest):
    with STATE_LOCK:
        approval = STATE["approval"]
        plan = STATE["pending_plan"]
        if approval_id != approval["id"]:
            raise HTTPException(status_code=409, detail="Recommendation changed. Refresh and review it.")
        if (
            approval["status"] != "PENDING"
            or plan is None
            or plan["approval_id"] != approval_id
        ):
            raise HTTPException(status_code=409, detail="No pending recommendation for this decision.")
        action = plan["schedule_action"]
        if action not in {"proceed", "relocate", "reschedule"}:
            raise HTTPException(status_code=409, detail="Unsupported scheduling action.")
        if plan["requires_human_approval"] is not True:
            raise HTTPException(status_code=409, detail="Invalid human-approval boundary.")

        decided_at = now_iso()
        approval.update({
            "status": request.decision.upper(),
            "actor": request.actor,
            "note": request.note,
            "decided_at": decided_at,
        })
        if request.decision == "approve":
            if action == "reschedule":
                STATE["scene"]["status"] = "RESCHEDULE_REQUIRED"
                STATE["digital_twin"]["schedule"] = "Rescheduling approved — date pending"
                decision_status = "Rescheduling approved — date pending"
            elif action == "relocate":
                STATE["scene"]["status"] = "RELOCATION_REQUIRED"
                decision_status = "Relocation approved — destination pending confirmation"
            else:
                STATE["scene"]["status"] = "PLAN_APPROVED"
                decision_status = "Approved — existing production plan retained"
            # Record authorization, not completed assignments, spending or risk reduction.
            STATE["digital_twin"]["last_updated"] = decided_at
            STATE["digital_twin"]["decision_status"] = decision_status
            message = decision_status
        else:
            # No changes to the production state or Digital Twin on rejection.
            message = "Recommendation rejected; existing production plan retained"

        event = append_event(
            "digital_twin" if request.decision == "approve" else "approval",
            message,
            {
                "approval_id": approval_id,
                "decision": request.decision,
                "actor": request.actor,
                "note": request.note,
                "decided_at": decided_at,
                "approved_plan" if request.decision == "approve" else "rejected_plan": deepcopy(plan),
            },
        )
        STATE["pending_plan"] = None
        return deepcopy({
            "approval": approval,
            "digital_twin": STATE["digital_twin"],
            "event": event,
        })


@app.post("/api/demo/reset")
def reset_demo():
    with STATE_LOCK:
        clear_pending("AWAITING_ANALYSIS")
        STATE["scene"] = deepcopy(INITIAL_SCENE)
        STATE["digital_twin"] = deepcopy(INITIAL_TWIN)
        append_event("system", "Demo reset; run analysis before requesting approval")
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
