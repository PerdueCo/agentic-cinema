"""Unit test for ResearchAgent.investigate.

Both external calls (Parallel, Gemini) are mocked so this runs in CI without
real API keys. The point of this test is to lock in the contract: given a
search result and a Gemini response, the agent returns a populated
ResearchFinding with the summary and source carried through correctly.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.agents.research_agent import ResearchAgent
from src.shared.schemas import SceneLocation, WeatherDisruptionEvent


@pytest.mark.asyncio
async def test_investigate_returns_grounded_finding(monkeypatch):
    agent = ResearchAgent(parallel_api_key="test", gemini_api_key="test")

    fake_result = SimpleNamespace(
        results=[
            SimpleNamespace(
                url="https://example.com/weather",
                excerpts=["Storm warning issued for the Big Sur coastline."],
            )
        ]
    )
    agent._parallel.beta.search = AsyncMock(return_value=fake_result)

    fake_response = SimpleNamespace(
        text="A storm warning is active near the shoot location; exteriors are at risk."
    )
    agent._gemini.models.generate_content = MagicMock(return_value=fake_response)

    event = WeatherDisruptionEvent(
        location=SceneLocation(
            location_id="loc-001",
            name="Coastal Cliff Set",
            city="Big Sur",
            country="USA",
        ),
        condition="storm warning",
        scheduled_date="2026-09-12",
    )

    finding = await agent.investigate(event)

    assert finding.source_url == "https://example.com/weather"
    assert "storm" in finding.summary.lower()
    agent._parallel.beta.search.assert_called_once()
    agent._gemini.models.generate_content.assert_called_once()
