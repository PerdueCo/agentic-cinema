import pytest
from unittest.mock import MagicMock, patch
from src.shared.agent_factory import create_scene42_orchestrator
from src.orchestrator import Scene42Orchestrator
from src.agents.budget_agent import BudgetAgent
from src.agents.producer_agent import ProducerAgent
from src.agents.research_agent import ResearchAgent
from src.agents.scheduling_agent import SchedulingAgent

def test_agent_factory_constructs_correct_agents():
    # Sentinels
    mock_research = MagicMock()
    mock_scheduling = MagicMock()
    mock_budget = MagicMock()
    mock_producer = MagicMock()

    # Patch constructors
    with patch("src.shared.agent_factory.ResearchAgent", return_value=mock_research) as p_res, \
         patch("src.shared.agent_factory.SchedulingAgent", return_value=mock_scheduling) as p_sch, \
         patch("src.shared.agent_factory.BudgetAgent", return_value=mock_budget) as p_bud, \
         patch("src.shared.agent_factory.ProducerAgent", return_value=mock_producer) as p_pro:

        orchestrator = create_scene42_orchestrator()

        # Assert constructors called exactly once
        p_res.assert_called_once()
        p_sch.assert_called_once()
        p_bud.assert_called_once()
        p_pro.assert_called_once()

    # Assertions
    assert isinstance(orchestrator, Scene42Orchestrator)
    assert orchestrator._research_agent is mock_research
    assert orchestrator._scheduling_agent is mock_scheduling
    assert orchestrator._budget_agent is mock_budget
    assert orchestrator._producer_agent is mock_producer
