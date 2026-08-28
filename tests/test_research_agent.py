"""Unit test for ResearchAgent.investigate.

Both external calls (Parallel, Gemini) are mocked so this runs in CI without
real API keys. The point of this test is to lock in the contract: given a
search result and a Gemini response, the agent returns a populated
ResearchFinding with the summary and source carried through correctly.
"""

from __future__ import annotations

import os
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agents.research_agent import ResearchAgent
from src.shared.schemas import SceneLocation, WeatherDisruptionEvent


def test_research_agent_default_vertex_client(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-project")
    monkeypatch.setenv("GOOGLE_CLOUD_LOCATION", "us-east1")
    with patch("google.genai.Client") as mock_client_class, \
         patch("src.agents.research_agent.AsyncParallel") as mock_parallel_class:
        _ = ResearchAgent(parallel_api_key="test-parallel")
        mock_client_class.assert_called_once_with(
            vertexai=True,
            project="test-project",
            location="us-east1",
        )
        mock_parallel_class.assert_called_once_with(
            api_key="test-parallel"
        )


@pytest.mark.asyncio
async def test_investigate_returns_grounded_finding(monkeypatch):
    mock_gemini = MagicMock()
    fake_response = SimpleNamespace(
        text="A storm warning is active near the shoot location; exteriors are at risk."
    )
    mock_gemini.models.generate_content.return_value = fake_response

    mock_parallel = MagicMock()
    fake_result = SimpleNamespace(
        results=[
            SimpleNamespace(
                url="https://example.com/weather",
                excerpts=["Storm warning issued for the Big Sur coastline."],
            )
        ]
    )
    mock_parallel.search = AsyncMock(return_value=fake_result)

    with patch("src.agents.research_agent.AsyncParallel", return_value=mock_parallel):
        agent = ResearchAgent(parallel_api_key="test", gemini_client=mock_gemini)

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
    mock_parallel.search.assert_awaited_once()
    search_kwargs = mock_parallel.search.await_args.kwargs
    assert search_kwargs["mode"] == "turbo"
    assert search_kwargs["max_chars_total"] == 6000
    assert "processor" not in search_kwargs
    assert "max_results" not in search_kwargs
    mock_gemini.models.generate_content.assert_called_once()
