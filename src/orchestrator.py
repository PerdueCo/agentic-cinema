"""Orchestration service for the fixed Scene 42 four-agent workflow.

The orchestrator coordinates AI recommendations only. It does not approve
the recommendation or update the Digital Twin. Those actions remain behind
the application's human-approval boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.shared.schemas import (
    BudgetAssessment,
    ProducerRecommendation,
    ResearchFinding,
    ScheduleRecommendation,
    WeatherDisruptionEvent,
)


@dataclass(frozen=True)
class Scene42WorkflowResult:
    """Complete evidence package presented for human approval."""

    event: WeatherDisruptionEvent
    research: ResearchFinding
    schedule: ScheduleRecommendation
    budget: BudgetAssessment
    producer: ProducerRecommendation
    requires_human_approval: bool = True


class Scene42Orchestrator:
    """Runs Research, Scheduling, Budget, and Producer in sequence."""

    def __init__(
        self,
        research_agent: Any,
        scheduling_agent: Any,
        budget_agent: Any,
        producer_agent: Any,
    ) -> None:
        self._research_agent = research_agent
        self._scheduling_agent = scheduling_agent
        self._budget_agent = budget_agent
        self._producer_agent = producer_agent

    async def run(
        self, event: WeatherDisruptionEvent
    ) -> Scene42WorkflowResult:
        """Produce a recommendation package without changing production state."""

        research = await self._research_agent.investigate(event)
        schedule = self._scheduling_agent.recommend(event, research)
        budget = self._budget_agent.assess(event, schedule)
        producer = self._producer_agent.recommend(
            event,
            research,
            schedule,
            budget,
        )

        return Scene42WorkflowResult(
            event=event,
            research=research,
            schedule=schedule,
            budget=budget,
            producer=producer,
        )
