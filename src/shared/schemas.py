"""Shared data contracts used across Digital Twin agents.

Keeping these as plain dataclasses (rather than scattering dicts through the
codebase) means every agent — Research, Scheduling, Budget, Producer — reads
and writes the same shape of object as it moves through the pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class SceneLocation:
    """A shoot location tied to one or more scenes in the production."""

    location_id: str
    name: str
    city: str
    country: str
    scene_ids: list[str] = field(default_factory=list)


@dataclass
class ResearchFinding:
    """A single grounded fact returned by the Research Agent.

    `source_url` and `excerpt` are kept so the Producer Agent's eventual
    recommendation can cite where a fact came from — useful both for the
    human-in-the-loop review step and for judges/reviewers checking that the
    agent's output is grounded rather than hallucinated.
    """

    query: str
    summary: str
    source_url: str | None
    excerpt: str | None
    retrieved_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ScheduleRecommendation:
    """Output of the Scheduling Agent.

    `suggested_action` is deliberately a plain string rather than an enum —
    Gemini's raw decision word — so a human reviewer can see exactly what
    the model said rather than a value that's already been coerced into a
    fixed category. The Budget Agent reads `suggested_action` to decide
    whether it needs to price out a reschedule or relocation.
    """

    affected_scene_ids: list[str]
    reasoning: str
    suggested_action: str
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class BudgetAssessment:
    """Output of the Budget Agent.

    `estimated_cost_impact` stays a string (e.g. "$3,000-$5,000") rather
    than a number, because without real day-rate and crew-size data wired
    in yet, Gemini is producing an informed estimate, not a calculation.
    Representing it as a precise float would overstate the agent's actual
    certainty — the string keeps that honest.
    """

    estimated_cost_impact: str
    reasoning: str
    recommended_action: str
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ProducerRecommendation:
    """Output of the Producer Agent — the final synthesis a human approves.

    This is the one recommendation a human actually reads and acts on.
    Everything upstream (Research, Scheduling, Budget) feeds into it, so
    the human reviews a single coherent call instead of three separate
    agent outputs on their own.
    """

    final_decision: str
    summary: str
    rationale: str
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class WeatherDisruptionEvent:
    """The seed event for the demonstration story described in the README."""

    location: SceneLocation
    condition: str
    scheduled_date: str
    findings: list[ResearchFinding] = field(default_factory=list)
    raw_payload: dict[str, Any] = field(default_factory=dict)