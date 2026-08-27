from src.agents.budget_agent import BudgetAgent
from src.agents.producer_agent import ProducerAgent
from src.agents.research_agent import ResearchAgent
from src.agents.scheduling_agent import SchedulingAgent
from src.orchestrator import Scene42Orchestrator

def create_scene42_orchestrator() -> Scene42Orchestrator:
    """Side-effect-free factory for Scene42 agents and orchestrator."""
    return Scene42Orchestrator(
        research_agent=ResearchAgent(),
        scheduling_agent=SchedulingAgent(),
        budget_agent=BudgetAgent(),
        producer_agent=ProducerAgent(),
    )
