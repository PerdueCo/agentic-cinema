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

    assert event.evidence_mode == "current_conditions"
    finding = await agent.investigate(event)
    assert "current weather" in finding.query

    assert finding.source_url == "https://example.com/weather"
    assert "storm" in finding.summary.lower()
    mock_parallel.search.assert_awaited_once()
    search_kwargs = mock_parallel.search.await_args.kwargs
    assert search_kwargs["mode"] == "turbo"
    assert search_kwargs["max_chars_total"] == 6000
    assert "processor" not in search_kwargs
    assert "max_results" not in search_kwargs
    mock_gemini.models.generate_content.assert_called_once()


@pytest.fixture
def historical_event():
    return WeatherDisruptionEvent(
        location=SceneLocation("scene-loc", "Exterior", "Atlanta", "USA"),
        condition="Downtown Atlanta EF2 tornado",
        scheduled_date="2008-03-14",
        evidence_mode="historical_replay",
        raw_payload={
            "wind_mph": 130,
            "historical_metadata": {
                "event_date": "2008-03-14", "event_time_local": "9:38 PM",
                "area": "Downtown Atlanta", "city": "Atlanta", "state": "Georgia",
                "country": "USA", "tornado_rating": "EF2",
                "estimated_max_wind_mph": 130,
                "reference_urls": ["https://example.com/reference-only"],
            },
        },
    )


@pytest.fixture
def replay_clients():
    gemini = MagicMock()
    gemini.models.generate_content.return_value = SimpleNamespace(
        text="The excerpt describes a past tornado in Atlanta. Damage was reported."
    )
    parallel = MagicMock()
    parallel.search = AsyncMock()
    with patch("src.agents.research_agent.AsyncParallel", return_value=parallel):
        agent = ResearchAgent(parallel_api_key="test", gemini_client=gemini)
    return agent, parallel, gemini


@pytest.mark.asyncio
async def test_historical_exact_query_and_runtime_evidence(historical_event, replay_clients):
    agent, parallel, gemini = replay_clients
    excerpt = "On March 14, 2008, a tornado struck Downtown Atlanta."
    parallel.search.return_value = SimpleNamespace(results=[
        SimpleNamespace(url="https://example.com/unrelated", excerpts=["August weather"]),
        SimpleNamespace(url="https://example.com/actual-result", excerpts=[excerpt]),
    ])
    finding = await agent.investigate(historical_event)
    parallel.search.assert_awaited_once()
    query = parallel.search.await_args.kwargs["objective"]
    assert "2008-03-14" in query and "Downtown Atlanta" in query
    assert "Georgia" in query and "USA" in query
    assert "current weather" not in query.lower()
    assert parallel.search.await_args.kwargs["search_queries"] == [query]
    assert finding.source_url == "https://example.com/actual-result"
    assert finding.excerpt == excerpt
    assert finding.retrieved_at.tzinfo is not None
    gemini.models.generate_content.assert_called_once()
    prompt = gemini.models.generate_content.call_args.kwargs["contents"]
    assert "2008-03-14" in prompt and "fictional production" in prompt
    assert excerpt in prompt
    assert "human verification required" in finding.summary


@pytest.mark.asyncio
@pytest.mark.parametrize("excerpt", [
    "Atlanta weather was generally sunny during August.",
    "A tornado struck Atlanta on March 15, 2008.",
    "A tornado struck New York on March 14, 2008.",
    "",
])
async def test_historical_unmatched_evidence_not_confirmed(
    historical_event, replay_clients, excerpt
):
    agent, parallel, gemini = replay_clients
    parallel.search.return_value = SimpleNamespace(results=[
        SimpleNamespace(url="https://example.com/weather", excerpts=[excerpt])
    ])
    finding = await agent.investigate(historical_event)
    assert "not confirmed" in finding.summary
    assert finding.source_url is None and finding.excerpt is None
    gemini.models.generate_content.assert_not_called()


@pytest.mark.asyncio
async def test_historical_empty_search_not_confirmed(historical_event, replay_clients):
    agent, parallel, gemini = replay_clients
    parallel.search.return_value = SimpleNamespace(results=[])
    finding = await agent.investigate(historical_event)
    assert "not confirmed" in finding.summary
    gemini.models.generate_content.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("field,value", [
    ("event_date", "2026-08-29"), ("event_date", "invalid"),
    ("city", "New York"), ("country", "Canada"), ("area", "   "),
    ("estimated_max_wind_mph", 99), ("estimated_max_wind_mph", None),
    ("reference_urls", []),
])
async def test_historical_inconsistent_metadata_before_calls(
    historical_event, replay_clients, field, value
):
    agent, parallel, gemini = replay_clients
    historical_event.raw_payload["historical_metadata"][field] = value
    with pytest.raises(ValueError):
        await agent.investigate(historical_event)
    parallel.search.assert_not_awaited()
    gemini.models.generate_content.assert_not_called()


@pytest.mark.asyncio
async def test_historical_missing_metadata_before_calls(historical_event, replay_clients):
    agent, parallel, gemini = replay_clients
    historical_event.raw_payload.pop("historical_metadata")
    with pytest.raises(ValueError):
        await agent.investigate(historical_event)
    parallel.search.assert_not_awaited()
    gemini.models.generate_content.assert_not_called()


@pytest.mark.asyncio
async def test_historical_zero_wind_is_not_missing(historical_event, replay_clients):
    agent, parallel, gemini = replay_clients
    historical_event.raw_payload["wind_mph"] = 0
    historical_event.raw_payload["historical_metadata"]["estimated_max_wind_mph"] = 0
    parallel.search.return_value = SimpleNamespace(results=[])
    await agent.investigate(historical_event)
    parallel.search.assert_awaited_once()
