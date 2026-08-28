import os
from typing import Any
from vertexai import agent_engines
from google.adk.agents import Agent
from pydantic import TypeAdapter
from src.shared.agent_factory import create_scene42_orchestrator
from src.shared.schemas import WeatherDisruptionEvent
from src.orchestrator import Scene42WorkflowResult

async def run_scene42_workflow(event_data: dict[str, Any]) -> dict[str, Any]:
    """Executes the Scene 42 orchestrator workflow."""
    # Convert input dict to WeatherDisruptionEvent
    # Validate the input dictionary into the nested Scene 42 dataclasses.
    event_adapter = TypeAdapter(WeatherDisruptionEvent)
    event = event_adapter.validate_python(event_data)

    # Instantiate orchestrator inside the tool
    orchestrator = create_scene42_orchestrator()
    result = await orchestrator.run(event)

    # Return JSON-serializable dictionary
    result_adapter = TypeAdapter(Scene42WorkflowResult)
    return result_adapter.dump_python(result, mode="json")

def configure_model_location() -> None:
    model_location = os.getenv("SCENE42_MODEL_LOCATION")
    if model_location:
        os.environ["GOOGLE_CLOUD_LOCATION"] = model_location

configure_model_location()

# Define the root Agent
root_agent = Agent(
    name="scene_42_root_agent",
    model=os.getenv("GEMINI_MODEL", "gemini-3.6-flash"),
    instruction="Use the single Scene 42 tool to process production disruption events.",
    tools=[run_scene42_workflow],
)

def create_adk_app() -> agent_engines.AdkApp:
    """Create the managed ADK application after cloud authentication."""
    return agent_engines.AdkApp(agent=root_agent)
