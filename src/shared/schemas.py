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
class WeatherDisruptionEvent:
    """The seed event for the demonstration story described in the README."""

    location: SceneLocation
    condition: str
    scheduled_date: str
    findings: list[ResearchFinding] = field(default_factory=list)
    raw_payload: dict[str, Any] = field(default_factory=dict)