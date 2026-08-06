#!/usr/bin/env python3
r"""
bootstrap_agentic_studio_v2.py

Creates, audits, and manages the Agentic Studio Digital Twin repository.

Default Windows project location:
    C:\Users\cash america\Documents\Projects\Agentic-Cinema

PowerShell examples:
    python .\bootstrap_agentic_studio_v2.py create
    python .\bootstrap_agentic_studio_v2.py create --init-git
    python .\bootstrap_agentic_studio_v2.py audit
    python .\bootstrap_agentic_studio_v2.py health
    python .\bootstrap_agentic_studio_v2.py watch
    python .\bootstrap_agentic_studio_v2.py add-file "docs\security\SecurityArchitecture.md"
    python .\bootstrap_agentic_studio_v2.py add-folder "docs\security"

Main features:
- Windows-safe paths and docstrings.
- Better error handling.
- Optional Git initialization.
- LICENSE and CHANGELOG generation.
- Professional README generation.
- Structure audit and project health checker.
- Project maturity score from 0 to 100.
- Project Manager audit for documents, diagrams, agents, architecture,
  tests, wiki pages, security, cloud, and demo readiness.
- Colorized PowerShell output.
- Markdown and JSON reports.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Iterable, Sequence

DEFAULT_ROOT = Path(r"C:\Users\cash america\Documents\Projects\Agentic-Cinema")
SCRIPT_VERSION = "2.0.0"

# ANSI color support. Modern PowerShell supports this.
class Color:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    CYAN = "\033[36m"
    MAGENTA = "\033[35m"
    GRAY = "\033[90m"


def supports_color() -> bool:
    if os.getenv("NO_COLOR"):
        return False
    if not sys.stdout.isatty():
        return False
    return True


USE_COLOR = supports_color()


def paint(text: str, color: str) -> str:
    return f"{color}{text}{Color.RESET}" if USE_COLOR else text


def info(message: str) -> None:
    print(paint(f"[INFO] {message}", Color.CYAN))


def ok(message: str) -> None:
    print(paint(f"[OK] {message}", Color.GREEN))


def warn(message: str) -> None:
    print(paint(f"[WARN] {message}", Color.YELLOW))


def fail(message: str) -> None:
    print(paint(f"[ERROR] {message}", Color.RED), file=sys.stderr)


def heading(message: str) -> None:
    print()
    print(paint("=" * 78, Color.BLUE))
    print(paint(message, Color.BOLD + Color.BLUE))
    print(paint("=" * 78, Color.BLUE))


README_CONTENT = """# Agentic Studio Digital Twin

> From vision to autonomous studio.

Agentic Studio Digital Twin is an AI-powered representation of a movie
production where autonomous AI agents collaborate to plan, monitor, explain,
and optimize filmmaking from script to release.

Instead of demonstrating only a chatbot, this project demonstrates a living
movie studio built around a shared Digital Twin.

## Core Vision

The platform models:

- Movies, scripts, scenes, and shots
- Actors, crew, locations, equipment, lighting, audio, and props
- Budgets, schedules, weather, and production status
- Editing, visual effects, marketing, and distribution

Each Digital Twin object can contain:

- Identity
- Metadata
- Relationships
- Current state
- History
- Events
- AI observations
- AI recommendations
- Human decisions

## Demonstration Story

A weather condition changes.

1. The Digital Twin receives the weather event.
2. The Scheduling Agent detects affected scenes and locations.
3. The Budget Agent calculates the financial impact.
4. The Producer Agent recommends options.
5. A human reviews and approves the decision.
6. The Digital Twin records the updated plan and audit history.

## Technology Direction

- Google Cloud
- Gemini
- Google Cloud Agent Builder
- IBM Bob
- Optional real-time Confluent event integration
- Python and FastAPI backend
- React and TypeScript frontend
- Human-in-the-loop approvals
- Explainable AI recommendations
- Event-driven Digital Twin architecture

## Project Navigation

- [Vision](docs/vision/Vision.md)
- [Mission](docs/vision/Mission.md)
- [Roadmap](docs/roadmap/Production_Roadmap.md)
- [Enterprise Architecture](docs/architecture/EnterpriseArchitecture.md)
- [AI Agent Architecture](docs/architecture/AIAgentArchitecture.md)
- [Digital Twin Architecture](docs/architecture/DigitalTwinArchitecture.md)
- [Digital Twin Overview](docs/digital-twin/DigitalTwinOverview.md)
- [Developer Onboarding](docs/onboarding/NewDeveloperGuide.md)
- [Mentor Guide](docs/onboarding/MentorGuide.md)
- [Project Check-Off Sheet](PROJECT_CHECKLIST.md)
- [Project Manager Audit](reports/PROJECT_MANAGER_AUDIT.md)

## Repository Layout

```text
Agentic-Cinema/
├── docs/
├── diagrams/
├── images/
├── examples/
├── templates/
├── presentations/
├── src/
├── tests/
├── scripts/
├── reports/
└── .github/
```

## Local Bootstrap

```powershell
python .\\bootstrap_agentic_studio_v2.py create
python .\\bootstrap_agentic_studio_v2.py audit
python .\\bootstrap_agentic_studio_v2.py health
```

## Project Status

Run the repository manager to regenerate the checklist, health report,
maturity score, and project-manager recommendations.

## License

See [LICENSE](LICENSE).
"""

LICENSE_CONTENT = """MIT License

Copyright (c) 2026 PerdueCo

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

CHANGELOG_CONTENT = f"""# Changelog

All notable changes to the Agentic Studio Digital Twin repository are recorded
in this file.

## [Unreleased]

### Added

- Repository bootstrap utility Version {SCRIPT_VERSION}
- Repository health checker
- Project maturity score
- Project Manager audit
- Required-document and required-diagram checks
- AI-agent documentation checks
- Wiki, testing, security, and deployment readiness checks
- Optional Git initialization
- Colorized PowerShell output
- Markdown and JSON reports

## [0.1.0] - 2026-08-06

### Added

- Initial Agentic Studio Digital Twin repository structure
- Vision, roadmap, architecture, Digital Twin, agent, onboarding, and wiki areas
"""

STARTER_FILES: dict[str, str] = {
    "README.md": README_CONTENT,
    "LICENSE": LICENSE_CONTENT,
    "CHANGELOG.md": CHANGELOG_CONTENT,
    "docs/vision/Vision.md": """# Vision

Create a living digital movie studio—not merely a chatbot—where autonomous AI
agents collaborate through a shared Digital Twin from script to release.
""",
    "docs/vision/Mission.md": """# Mission

Help filmmaking teams make faster, safer, explainable, and better-informed
production decisions while preserving human approval and creative control.
""",
    "docs/vision/Production_Guide.md": """# Production Guide

Describe the full movie-production lifecycle represented by the platform.
""",
    "docs/roadmap/Production_Roadmap.md": """# Production Roadmap

- [ ] ACT I — The Vision
- [ ] ACT II — Pre-Production
- [ ] ACT III — Lights, Camera, Code
- [ ] ACT IV — Post-Production
- [ ] ACT V — The Premiere
- [ ] ACT VI — The Franchise
""",
    "docs/architecture/EnterpriseArchitecture.md": "# Enterprise Architecture\n\nDescribe the platform, users, external systems, security zones, and major components.\n",
    "docs/architecture/AIAgentArchitecture.md": "# AI Agent Architecture\n\nDescribe agent roles, orchestration, memory, tools, guardrails, and approvals.\n",
    "docs/architecture/DigitalTwinArchitecture.md": "# Digital Twin Architecture\n\nDescribe identity, metadata, relationships, state, history, events, observations, and recommendations.\n",
    "docs/architecture/DataFlowArchitecture.md": "# Data Flow Architecture\n\nDescribe production events and data movement across the studio.\n",
    "docs/architecture/CloudArchitecture.md": "# Cloud Architecture\n\nDescribe Google Cloud, Gemini, Agent Builder, IBM Bob, and optional Confluent components.\n",
    "docs/architecture/SecurityArchitecture.md": "# Security Architecture\n\nDescribe identity, secrets, least privilege, audit logging, approvals, and data protection.\n",
    "docs/digital-twin/DigitalTwinOverview.md": """# Digital Twin Overview

The Digital Twin models movies, scripts, scenes, shots, actors, crew,
locations, equipment, lighting, audio, props, budgets, schedules, weather,
production status, editing, visual effects, marketing, and distribution.
""",
    "docs/digital-twin/MovieModel.md": "# Movie Model\n\nDefine movie, script, scene, and shot entities.\n",
    "docs/digital-twin/ProductionObjects.md": "# Production Objects\n\nDefine cast, crew, locations, equipment, props, schedules, budgets, and production status.\n",
    "docs/digital-twin/AIObservationModel.md": "# AI Observation Model\n\nDefine evidence, confidence, observations, recommendations, risks, and human decisions.\n",
    "docs/ai-agents/DirectorAgent.md": "# Director Agent\n\n## Purpose\n\n## Inputs\n\n## Tools\n\n## Outputs\n\n## Approval Boundaries\n",
    "docs/ai-agents/ProducerAgent.md": "# Producer Agent\n\n## Purpose\n\n## Inputs\n\n## Tools\n\n## Outputs\n\n## Approval Boundaries\n",
    "docs/ai-agents/SchedulingAgent.md": "# Scheduling Agent\n\n## Purpose\n\n## Inputs\n\n## Tools\n\n## Outputs\n\n## Approval Boundaries\n",
    "docs/ai-agents/BudgetAgent.md": "# Budget Agent\n\n## Purpose\n\n## Inputs\n\n## Tools\n\n## Outputs\n\n## Approval Boundaries\n",
    "docs/ai-agents/WeatherAgent.md": "# Weather Agent\n\n## Purpose\n\n## Inputs\n\n## Tools\n\n## Outputs\n\n## Approval Boundaries\n",
    "docs/ai-agents/MarketingAgent.md": "# Marketing Agent\n\n## Purpose\n\n## Inputs\n\n## Tools\n\n## Outputs\n\n## Approval Boundaries\n",
    "docs/engineering/EngineeringPrompt.md": "# Master Engineering Prompt\n\nPlace the approved multidisciplinary engineering prompt here.\n",
    "docs/engineering/CodingStandards.md": "# Coding Standards\n\nDocument naming, formatting, testing, security, logging, and review rules.\n",
    "docs/engineering/DevelopmentGuide.md": "# Development Guide\n\nDocument the local development and pull-request workflow.\n",
    "docs/onboarding/NewDeveloperGuide.md": "# New Developer Guide\n\nExplain setup, architecture, first task, testing, and pull requests.\n",
    "docs/onboarding/MentorGuide.md": "# Mentor Guide\n\nExplain project context, feedback areas, meeting format, and hackathon boundaries.\n",
    "docs/onboarding/EnvironmentSetup.md": "# Environment Setup\n\nDocument Python, Node.js, Docker, Google Cloud, IBM Bob, and environment variables.\n",
    "docs/api/API.md": "# API\n\nDocument endpoints, requests, responses, errors, and authentication.\n",
    "docs/api/Events.md": "# Events\n\nDocument Digital Twin events and agent-triggering rules.\n",
    "docs/deployment/LocalSetup.md": "# Local Setup\n\nDocument local startup and shutdown instructions.\n",
    "docs/deployment/GoogleCloud.md": "# Google Cloud Deployment\n\nDocument cloud resources and deployment steps.\n",
    "docs/deployment/CI-CD.md": "# CI/CD\n\nDocument automated build, test, security, and deployment workflows.\n",
    "docs/wiki/FAQ.md": "# Frequently Asked Questions\n",
    "docs/wiki/Glossary.md": "# Glossary\n\nDefine Agentic AI, Digital Twin, event, recommendation, and human-in-the-loop.\n",
    "docs/wiki/LessonsLearned.md": "# Lessons Learned\n\nCapture technical, product, teamwork, and hackathon lessons.\n",
    "docs/wiki/DecisionLog.md": "# Decision Log\n\nRecord important architecture, product, scope, and team decisions.\n",
    "templates/ArchitectureTemplate.md": "# Architecture Title\n\n## Purpose\n\n## Components\n\n## Data Flow\n\n## Security\n\n## Decisions\n",
    "templates/AgentTemplate.md": "# Agent Name\n\n## Purpose\n\n## Inputs\n\n## Tools\n\n## Outputs\n\n## Approval Boundaries\n",
    "templates/DesignTemplate.md": "# Design Title\n\n## User\n\n## Problem\n\n## Flow\n\n## Acceptance Criteria\n",
    "templates/StoryTemplate.md": "# User Story\n\nAs a...\n\nI want...\n\nSo that...\n\n## Acceptance Criteria\n",
    "templates/MeetingNotes.md": "# Meeting Notes\n\n**Date:**\n\n**Attendees:**\n\n## Decisions\n\n## Actions\n",
    "tests/README.md": "# Tests\n\nAdd unit, integration, API, agent, Digital Twin, and demonstration tests here.\n",
    "scripts/README.md": "# Scripts\n\nStore setup, data generation, validation, deployment, and demo scripts here.\n",
    "examples/sample-weather/weather_event.json": """{
  "event_id": "weather-001",
  "type": "SEVERE_WEATHER_ALERT",
  "location": "Exterior Location A",
  "severity": "high",
  "recommended_action": "Evaluate schedule change"
}
""",
    "examples/sample-production/production_state.json": """{
  "movie_id": "movie-001",
  "title": "Sample Production",
  "status": "pre-production",
  "current_schedule_risk": "medium"
}
""",
    ".github/workflows/README.md": "# GitHub Actions\n\nPlace CI/CD workflow YAML files in this folder.\n",
    ".github/ISSUE_TEMPLATE/feature_request.md": """---
name: Feature request
about: Suggest an Agentic Studio improvement
---

## Problem

## Proposed Change

## Acceptance Criteria
""",
    ".gitignore": """# Python
__pycache__/
*.py[cod]
.venv/
venv/

# Node
node_modules/
dist/
build/

# Secrets
.env
.env.*
!.env.example
*.pem
*.key

# IDE and operating system
.vscode/
.idea/
.DS_Store
Thumbs.db

# Local reports
reports/*.tmp
""",
    ".env.example": """# Never commit real secrets.
GOOGLE_CLOUD_PROJECT=
GOOGLE_APPLICATION_CREDENTIALS=
GEMINI_API_KEY=
IBM_BOB_ENDPOINT=
CONFLUENT_BOOTSTRAP_SERVERS=
""",
}

REQUIRED_FOLDERS = [
    "docs/vision",
    "docs/roadmap",
    "docs/architecture",
    "docs/digital-twin",
    "docs/ai-agents",
    "docs/engineering",
    "docs/onboarding",
    "docs/api",
    "docs/deployment",
    "docs/wiki",
    "diagrams/enterprise",
    "diagrams/ai-agents",
    "diagrams/digital-twin",
    "diagrams/workflows",
    "diagrams/sequence",
    "images/dashboard",
    "images/architecture",
    "images/digital-twin",
    "images/presentations",
    "images/branding",
    "examples/sample-script",
    "examples/sample-production",
    "examples/sample-weather",
    "examples/sample-budget",
    "examples/sample-agents",
    "templates",
    "presentations/GoogleHackathon",
    "presentations/MentorReview",
    "presentations/InvestorPitch",
    "presentations/DemoDay",
    "src/frontend",
    "src/backend",
    "src/agents",
    "src/digital_twin",
    "src/services",
    "src/shared",
    "tests",
    "scripts",
    "reports",
    ".github/workflows",
    ".github/ISSUE_TEMPLATE",
]

PLACEHOLDER_FILES = {
    "src/frontend/.gitkeep": "",
    "src/backend/.gitkeep": "",
    "src/agents/.gitkeep": "",
    "src/digital_twin/.gitkeep": "",
    "src/services/.gitkeep": "",
    "src/shared/.gitkeep": "",
    "diagrams/enterprise/.gitkeep": "",
    "diagrams/ai-agents/.gitkeep": "",
    "diagrams/digital-twin/.gitkeep": "",
    "diagrams/workflows/.gitkeep": "",
    "diagrams/sequence/.gitkeep": "",
    "images/dashboard/.gitkeep": "",
    "images/architecture/.gitkeep": "",
    "images/digital-twin/.gitkeep": "",
    "images/presentations/.gitkeep": "",
    "images/branding/.gitkeep": "",
    "examples/sample-script/.gitkeep": "",
    "examples/sample-budget/.gitkeep": "",
    "examples/sample-agents/.gitkeep": "",
    "presentations/GoogleHackathon/.gitkeep": "",
    "presentations/MentorReview/.gitkeep": "",
    "presentations/InvestorPitch/.gitkeep": "",
    "presentations/DemoDay/.gitkeep": "",
}

IGNORED_NAMES = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    ".idea",
    ".vscode",
}

GENERATED_FILES = {
    "PROJECT_CHECKLIST.md",
    "reports/structure_audit.json",
    "reports/project_health.json",
    "reports/PROJECT_MANAGER_AUDIT.md",
}


@dataclass
class Check:
    category: str
    name: str
    path: str
    weight: int
    passed: bool
    recommendation: str


@dataclass
class HealthReport:
    generated_at: str
    project_root: str
    version: str
    maturity_score: int
    status: str
    checks_passed: int
    checks_total: int
    category_scores: dict[str, int]
    missing_required_folders: list[str]
    missing_required_files: list[str]
    unexpected_items: list[str]
    recommendations: list[str]
    checks: list[dict]


def normalize(path: Path) -> str:
    return path.as_posix().lstrip("./")


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def ensure_inside_root(root: Path, candidate: Path) -> None:
    try:
        candidate.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError("The requested path must remain inside the project root.") from exc


def create_structure(root: Path, overwrite: bool = False) -> tuple[int, int]:
    root.mkdir(parents=True, exist_ok=True)
    created = 0
    preserved = 0

    for folder in REQUIRED_FOLDERS:
        path = root / folder
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            created += 1

    for relative, content in {**STARTER_FILES, **PLACEHOLDER_FILES}.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and not overwrite:
            preserved += 1
            continue
        path.write_text(content, encoding="utf-8")
        created += 1

    return created, preserved


def git_available() -> bool:
    return shutil.which("git") is not None


def initialize_git(root: Path) -> tuple[bool, str]:
    if not git_available():
        return False, "Git is not installed or is not available in PATH."

    git_folder = root / ".git"
    if git_folder.exists():
        return True, "Git repository already initialized."

    result = subprocess.run(
        ["git", "init"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0:
        return True, result.stdout.strip() or "Git repository initialized."
    return False, result.stderr.strip() or "Git initialization failed."


def expected_paths() -> set[str]:
    return (
        set(REQUIRED_FOLDERS)
        | set(STARTER_FILES)
        | set(PLACEHOLDER_FILES)
        | GENERATED_FILES
    )


def list_actual_paths(root: Path) -> set[str]:
    actual: set[str] = set()
    if not root.exists():
        return actual

    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if any(part in IGNORED_NAMES for part in relative.parts):
            continue
        actual.add(normalize(relative))
    return actual


def find_unexpected(root: Path, expected: set[str]) -> list[str]:
    unexpected: list[str] = []

    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if any(part in IGNORED_NAMES for part in relative.parts):
            continue

        rel = normalize(relative)
        if rel in expected:
            continue

        prefix = rel.rstrip("/") + "/"
        if path.is_dir() and any(item.startswith(prefix) for item in expected):
            continue

        unexpected.append(rel + ("/" if path.is_dir() else ""))

    return sorted(unexpected, key=str.lower)


def structure_report(root: Path) -> dict:
    missing_folders = sorted(
        [item for item in REQUIRED_FOLDERS if not (root / item).is_dir()],
        key=str.lower,
    )
    required_files = list(STARTER_FILES) + list(PLACEHOLDER_FILES)
    missing_files = sorted(
        [item for item in required_files if not (root / item).is_file()],
        key=str.lower,
    )
    total = len(REQUIRED_FOLDERS) + len(required_files)
    present = total - len(missing_folders) - len(missing_files)
    completion = round((present / total) * 100, 1) if total else 100.0

    return {
        "generated_at": now_iso(),
        "project_root": str(root),
        "completion_percent": completion,
        "required_count": total,
        "present_count": present,
        "missing_folders": missing_folders,
        "missing_files": missing_files,
        "unexpected_items": find_unexpected(root, expected_paths()),
        "status": "PASS" if not missing_folders and not missing_files else "ACTION REQUIRED",
    }


def contains_meaningful_content(path: Path, minimum_chars: int = 80) -> bool:
    if not path.is_file():
        return False
    try:
        text = path.read_text(encoding="utf-8", errors="ignore").strip()
    except OSError:
        return False
    return len(text) >= minimum_chars


def folder_has_real_files(path: Path, extensions: Sequence[str] | None = None) -> bool:
    if not path.is_dir():
        return False

    for item in path.rglob("*"):
        if not item.is_file() or item.name == ".gitkeep":
            continue
        if extensions and item.suffix.lower() not in extensions:
            continue
        return True
    return False


def make_checks(root: Path) -> list[Check]:
    checks: list[Check] = []

    def add(
        category: str,
        name: str,
        relative: str,
        weight: int,
        passed: bool,
        recommendation: str,
    ) -> None:
        checks.append(
            Check(
                category=category,
                name=name,
                path=relative,
                weight=weight,
                passed=passed,
                recommendation=recommendation,
            )
        )

    # Foundation: 15 points
    add("Foundation", "Professional README", "README.md", 5,
        contains_meaningful_content(root / "README.md", 500),
        "Expand README.md with vision, architecture, demo flow, setup, and navigation.")
    add("Foundation", "License", "LICENSE", 3,
        (root / "LICENSE").is_file(),
        "Add a project license.")
    add("Foundation", "Changelog", "CHANGELOG.md", 3,
        contains_meaningful_content(root / "CHANGELOG.md", 100),
        "Track project changes in CHANGELOG.md.")
    add("Foundation", "Git ignore rules", ".gitignore", 2,
        (root / ".gitignore").is_file(),
        "Add .gitignore rules for Python, Node, secrets, and local files.")
    add("Foundation", "Environment template", ".env.example", 2,
        (root / ".env.example").is_file(),
        "Add .env.example without real secrets.")

    # Vision and roadmap: 10 points
    add("Vision", "Vision document", "docs/vision/Vision.md", 3,
        contains_meaningful_content(root / "docs/vision/Vision.md"),
        "Complete the vision document.")
    add("Vision", "Mission document", "docs/vision/Mission.md", 2,
        contains_meaningful_content(root / "docs/vision/Mission.md"),
        "Complete the mission document.")
    add("Vision", "Production guide", "docs/vision/Production_Guide.md", 2,
        contains_meaningful_content(root / "docs/vision/Production_Guide.md"),
        "Explain the movie-production lifecycle.")
    add("Vision", "Production roadmap", "docs/roadmap/Production_Roadmap.md", 3,
        contains_meaningful_content(root / "docs/roadmap/Production_Roadmap.md", 150),
        "Add milestones, dates, owners, and MVP scope to the roadmap.")

    # Architecture: 20 points
    architecture_files = [
        ("Enterprise architecture", "docs/architecture/EnterpriseArchitecture.md", 4),
        ("AI agent architecture", "docs/architecture/AIAgentArchitecture.md", 4),
        ("Digital Twin architecture", "docs/architecture/DigitalTwinArchitecture.md", 4),
        ("Data-flow architecture", "docs/architecture/DataFlowArchitecture.md", 3),
        ("Cloud architecture", "docs/architecture/CloudArchitecture.md", 3),
        ("Security architecture", "docs/architecture/SecurityArchitecture.md", 2),
    ]
    for name, relative, weight in architecture_files:
        add("Architecture", name, relative, weight,
            contains_meaningful_content(root / relative, 120),
            f"Complete {relative} with components, data flow, decisions, and risks.")

    # Digital Twin: 10 points
    twin_files = [
        ("Digital Twin overview", "docs/digital-twin/DigitalTwinOverview.md", 3),
        ("Movie model", "docs/digital-twin/MovieModel.md", 2),
        ("Production objects", "docs/digital-twin/ProductionObjects.md", 3),
        ("AI observation model", "docs/digital-twin/AIObservationModel.md", 2),
    ]
    for name, relative, weight in twin_files:
        add("Digital Twin", name, relative, weight,
            contains_meaningful_content(root / relative, 120),
            f"Complete {relative} with entities, state, relationships, history, and events.")

    # Agents: 10 points
    agent_folder = root / "docs/ai-agents"
    agent_docs = [
        path for path in agent_folder.glob("*Agent.md")
        if path.is_file() and contains_meaningful_content(path, 100)
    ] if agent_folder.exists() else []
    add("AI Agents", "At least four documented agents", "docs/ai-agents", 5,
        len(agent_docs) >= 4,
        "Document at least four MVP agents with purpose, inputs, tools, outputs, and approval boundaries.")
    add("AI Agents", "Weather Agent documented", "docs/ai-agents/WeatherAgent.md", 2,
        contains_meaningful_content(root / "docs/ai-agents/WeatherAgent.md", 100),
        "Document the Weather Agent used by the main demo.")
    add("AI Agents", "Agent source code started", "src/agents", 3,
        folder_has_real_files(root / "src/agents", [".py", ".ts", ".js"]),
        "Add the first executable agent implementation under src/agents.")

    # Diagrams: 10 points
    diagram_checks = [
        ("Enterprise diagram", "diagrams/enterprise", 2),
        ("AI-agent diagram", "diagrams/ai-agents", 2),
        ("Digital Twin diagram", "diagrams/digital-twin", 3),
        ("Workflow diagram", "diagrams/workflows", 2),
        ("Sequence diagram", "diagrams/sequence", 1),
    ]
    diagram_extensions = [".png", ".jpg", ".jpeg", ".svg", ".pdf", ".drawio", ".mmd", ".puml"]
    for name, relative, weight in diagram_checks:
        add("Diagrams", name, relative, weight,
            folder_has_real_files(root / relative, diagram_extensions),
            f"Add at least one diagram to {relative}.")

    # Engineering and testing: 10 points
    add("Engineering", "Coding standards", "docs/engineering/CodingStandards.md", 2,
        contains_meaningful_content(root / "docs/engineering/CodingStandards.md", 120),
        "Complete coding, testing, logging, review, and security standards.")
    add("Engineering", "Development guide", "docs/engineering/DevelopmentGuide.md", 2,
        contains_meaningful_content(root / "docs/engineering/DevelopmentGuide.md", 120),
        "Document the local development workflow.")
    add("Engineering", "Executable source started", "src", 2,
        folder_has_real_files(root / "src", [".py", ".ts", ".tsx", ".js", ".jsx"]),
        "Add executable frontend, backend, Digital Twin, or service code.")
    add("Engineering", "Automated tests started", "tests", 2,
        folder_has_real_files(root / "tests", [".py", ".ts", ".js"]),
        "Add at least one automated test.")
    add("Engineering", "CI workflow started", ".github/workflows", 2,
        folder_has_real_files(root / ".github/workflows", [".yml", ".yaml"]),
        "Add a GitHub Actions workflow for build, tests, and security checks.")

    # Wiki and onboarding: 5 points
    add("Knowledge", "Developer onboarding", "docs/onboarding/NewDeveloperGuide.md", 1,
        contains_meaningful_content(root / "docs/onboarding/NewDeveloperGuide.md", 120),
        "Complete developer onboarding.")
    add("Knowledge", "Mentor onboarding", "docs/onboarding/MentorGuide.md", 1,
        contains_meaningful_content(root / "docs/onboarding/MentorGuide.md", 120),
        "Complete mentor guidance and boundaries.")
    add("Knowledge", "FAQ", "docs/wiki/FAQ.md", 1,
        contains_meaningful_content(root / "docs/wiki/FAQ.md", 100),
        "Add common questions and answers.")
    add("Knowledge", "Glossary", "docs/wiki/Glossary.md", 1,
        contains_meaningful_content(root / "docs/wiki/Glossary.md", 100),
        "Define important Digital Twin and agent terms.")
    add("Knowledge", "Decision log", "docs/wiki/DecisionLog.md", 1,
        contains_meaningful_content(root / "docs/wiki/DecisionLog.md", 100),
        "Record major architecture and scope decisions.")

    # Demo readiness: 10 points
    add("Demo", "Weather event sample", "examples/sample-weather/weather_event.json", 2,
        (root / "examples/sample-weather/weather_event.json").is_file(),
        "Add a realistic weather event example.")
    add("Demo", "Production state sample", "examples/sample-production/production_state.json", 2,
        (root / "examples/sample-production/production_state.json").is_file(),
        "Add a sample production state.")
    add("Demo", "Demo script or workflow", "presentations/DemoDay", 2,
        folder_has_real_files(root / "presentations/DemoDay"),
        "Add the demo script, screenshots, or presentation.")
    add("Demo", "Frontend started", "src/frontend", 2,
        folder_has_real_files(root / "src/frontend", [".ts", ".tsx", ".js", ".jsx", ".html"]),
        "Start the visible Digital Twin dashboard.")
    add("Demo", "Backend started", "src/backend", 2,
        folder_has_real_files(root / "src/backend", [".py", ".ts", ".js"]),
        "Start the API or orchestration backend.")

    return checks


def calculate_health(root: Path, structure: dict) -> HealthReport:
    checks = make_checks(root)
    total_weight = sum(check.weight for check in checks)
    earned_weight = sum(check.weight for check in checks if check.passed)
    score = round((earned_weight / total_weight) * 100) if total_weight else 100

    category_totals: dict[str, int] = {}
    category_earned: dict[str, int] = {}
    for check in checks:
        category_totals[check.category] = category_totals.get(check.category, 0) + check.weight
        if check.passed:
            category_earned[check.category] = category_earned.get(check.category, 0) + check.weight

    category_scores = {
        category: round((category_earned.get(category, 0) / total) * 100)
        for category, total in category_totals.items()
    }

    recommendations = [
        check.recommendation for check in checks if not check.passed
    ]

    if score >= 90:
        status = "Demo Ready"
    elif score >= 75:
        status = "Strong Foundation"
    elif score >= 50:
        status = "Developing"
    elif score >= 25:
        status = "Early Build"
    else:
        status = "Initial Setup"

    return HealthReport(
        generated_at=now_iso(),
        project_root=str(root),
        version=SCRIPT_VERSION,
        maturity_score=score,
        status=status,
        checks_passed=sum(1 for check in checks if check.passed),
        checks_total=len(checks),
        category_scores=category_scores,
        missing_required_folders=structure["missing_folders"],
        missing_required_files=structure["missing_files"],
        unexpected_items=structure["unexpected_items"],
        recommendations=recommendations,
        checks=[asdict(check) for check in checks],
    )


def checkbox(value: bool) -> str:
    return "x" if value else " "


def group_items(items: Iterable[str]) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {}
    for item in sorted(items, key=str.lower):
        top = item.split("/", 1)[0]
        groups.setdefault(top, []).append(item)
    return groups


def write_structure_report(root: Path, report: dict) -> Path:
    path = root / "reports" / "structure_audit.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return path


def write_health_json(root: Path, report: HealthReport) -> Path:
    path = root / "reports" / "project_health.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(report), indent=2), encoding="utf-8")
    return path


def write_checklist(root: Path, structure: dict, health: HealthReport) -> Path:
    path = root / "PROJECT_CHECKLIST.md"
    lines = [
        "# Agentic Studio Repository Check-Off Sheet",
        "",
        f"**Last audit:** {health.generated_at}",
        f"**Project root:** `{health.project_root}`",
        f"**Structure status:** **{structure['status']}**",
        f"**Structure completion:** **{structure['completion_percent']}%**",
        f"**Project maturity:** **{health.maturity_score}% — {health.status}**",
        "",
        "## Run the Manager",
        "",
        "```powershell",
        r"python .\bootstrap_agentic_studio_v2.py audit",
        r"python .\bootstrap_agentic_studio_v2.py health",
        "```",
        "",
        "## Required Folders",
        "",
    ]

    for group, items in group_items(REQUIRED_FOLDERS).items():
        lines.append(f"### `{group}`")
        lines.append("")
        for item in items:
            lines.append(f"- [{checkbox((root / item).is_dir())}] `{item}/`")
        lines.append("")

    all_required_files = list(STARTER_FILES) + list(PLACEHOLDER_FILES)
    lines.extend(["## Required Files", ""])
    for group, items in group_items(all_required_files).items():
        lines.append(f"### `{group}`")
        lines.append("")
        for item in items:
            lines.append(f"- [{checkbox((root / item).is_file())}] `{item}`")
        lines.append("")

    lines.extend(["## Project Maturity Categories", ""])
    for category, score in sorted(health.category_scores.items()):
        lines.append(f"- [{checkbox(score == 100)}] **{category}: {score}%**")

    lines.extend(["", "## Missing Required Items", ""])
    missing = structure["missing_folders"] + structure["missing_files"]
    if missing:
        for item in missing:
            lines.append(f"- [ ] `{item}`")
    else:
        lines.append("- [x] No required folders or files are missing.")

    lines.extend(["", "## Added or Unexpected Items", ""])
    if structure["unexpected_items"]:
        for item in structure["unexpected_items"]:
            lines.append(f"- [ ] Review `{item}`")
    else:
        lines.append("- [x] No unexpected items found.")

    lines.extend(["", "## Highest-Priority Recommendations", ""])
    if health.recommendations:
        for recommendation in health.recommendations[:12]:
            lines.append(f"- [ ] {recommendation}")
    else:
        lines.append("- [x] No current recommendations.")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_project_manager_audit(root: Path, health: HealthReport) -> Path:
    path = root / "reports" / "PROJECT_MANAGER_AUDIT.md"
    failed_checks = [item for item in health.checks if not item["passed"]]

    lines = [
        "# Agentic Studio Project Manager Audit",
        "",
        f"**Generated:** {health.generated_at}",
        f"**Maturity score:** **{health.maturity_score}%**",
        f"**Status:** **{health.status}**",
        f"**Checks passed:** **{health.checks_passed} of {health.checks_total}**",
        "",
        "## Executive Summary",
        "",
    ]

    if health.maturity_score >= 90:
        lines.append(
            "The repository is structurally mature and close to demonstration readiness. "
            "Focus on rehearsal, evidence, reliability, and judge-facing clarity."
        )
    elif health.maturity_score >= 75:
        lines.append(
            "The project has a strong foundation. Complete the remaining executable demo, "
            "tests, diagrams, and presentation evidence."
        )
    elif health.maturity_score >= 50:
        lines.append(
            "The project is developing but still needs implementation evidence. Prioritize "
            "the weather-to-schedule-to-budget demonstration before expanding scope."
        )
    else:
        lines.append(
            "The repository foundation is being established. Concentrate on the core MVP, "
            "essential architecture, and one end-to-end working story."
        )

    lines.extend(["", "## Category Scores", ""])
    for category, score in sorted(health.category_scores.items()):
        lines.append(f"- **{category}:** {score}%")

    lines.extend(["", "## Missing Documents", ""])
    missing_docs = [
        item for item in failed_checks
        if item["path"].endswith(".md")
        and item["category"] not in {"Architecture", "AI Agents", "Knowledge"}
    ]
    if missing_docs:
        for item in missing_docs:
            lines.append(f"- [ ] `{item['path']}` — {item['recommendation']}")
    else:
        lines.append("- [x] No major general documents are missing.")

    lines.extend(["", "## Missing Architecture", ""])
    architecture = [item for item in failed_checks if item["category"] == "Architecture"]
    if architecture:
        for item in architecture:
            lines.append(f"- [ ] `{item['path']}` — {item['recommendation']}")
    else:
        lines.append("- [x] Architecture documentation meets the current checks.")

    lines.extend(["", "## Missing Diagrams", ""])
    diagrams = [item for item in failed_checks if item["category"] == "Diagrams"]
    if diagrams:
        for item in diagrams:
            lines.append(f"- [ ] `{item['path']}` — {item['recommendation']}")
    else:
        lines.append("- [x] Required diagram categories contain visual artifacts.")

    lines.extend(["", "## Missing or Incomplete Agents", ""])
    agents = [item for item in failed_checks if item["category"] == "AI Agents"]
    if agents:
        for item in agents:
            lines.append(f"- [ ] `{item['path']}` — {item['recommendation']}")
    else:
        lines.append("- [x] Agent documentation and initial implementation are present.")

    lines.extend(["", "## Missing Tests and Engineering Controls", ""])
    engineering = [item for item in failed_checks if item["category"] == "Engineering"]
    if engineering:
        for item in engineering:
            lines.append(f"- [ ] `{item['path']}` — {item['recommendation']}")
    else:
        lines.append("- [x] Engineering and testing controls meet the current checks.")

    lines.extend(["", "## Missing Wiki or Onboarding Pages", ""])
    knowledge = [item for item in failed_checks if item["category"] == "Knowledge"]
    if knowledge:
        for item in knowledge:
            lines.append(f"- [ ] `{item['path']}` — {item['recommendation']}")
    else:
        lines.append("- [x] Wiki and onboarding materials meet the current checks.")

    lines.extend(["", "## Demo Readiness Gaps", ""])
    demo = [item for item in failed_checks if item["category"] == "Demo"]
    if demo:
        for item in demo:
            lines.append(f"- [ ] `{item['path']}` — {item['recommendation']}")
    else:
        lines.append("- [x] Demo-readiness checks passed.")

    lines.extend(["", "## Scope Guardrail", ""])
    lines.append(
        "Do not add a new major feature unless it directly strengthens the working "
        "weather event → Digital Twin update → schedule impact → budget impact → "
        "agent recommendation → human approval demonstration."
    )

    lines.extend(["", "## Recommended Work Order", ""])
    priority = failed_checks[:10]
    if priority:
        for index, item in enumerate(priority, start=1):
            lines.append(f"{index}. {item['recommendation']}")
    else:
        lines.append("1. Rehearse the demo and collect screenshots, logs, and judge-facing evidence.")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def print_structure_summary(report: dict) -> None:
    heading("AGENTIC STUDIO STRUCTURE AUDIT")
    print(f"Root:       {report['project_root']}")
    print(f"Status:     {report['status']}")
    print(f"Completion: {report['completion_percent']}%")
    print(f"Required:   {report['present_count']} / {report['required_count']} present")

    if report["missing_folders"]:
        print()
        warn("Missing folders:")
        for item in report["missing_folders"]:
            print(f"  - {item}/")

    if report["missing_files"]:
        print()
        warn("Missing files:")
        for item in report["missing_files"]:
            print(f"  - {item}")

    if report["unexpected_items"]:
        print()
        warn("Added or unexpected items requiring review:")
        for item in report["unexpected_items"]:
            print(f"  - {item}")

    if not report["missing_folders"] and not report["missing_files"]:
        ok("All required folders and files are present.")


def print_health_summary(report: HealthReport) -> None:
    heading("AGENTIC STUDIO PROJECT HEALTH")
    color = (
        Color.GREEN if report.maturity_score >= 75
        else Color.YELLOW if report.maturity_score >= 50
        else Color.RED
    )
    print(f"Maturity score: {paint(str(report.maturity_score) + '%', color)}")
    print(f"Status:         {paint(report.status, color)}")
    print(f"Checks passed:  {report.checks_passed} / {report.checks_total}")
    print()
    print("Category scores:")
    for category, score in sorted(report.category_scores.items()):
        category_color = Color.GREEN if score >= 80 else Color.YELLOW if score >= 50 else Color.RED
        print(f"  {category:<16} {paint(str(score) + '%', category_color)}")

    if report.recommendations:
        print()
        warn("Top recommendations:")
        for recommendation in report.recommendations[:8]:
            print(f"  - {recommendation}")
    else:
        print()
        ok("All current project health checks passed.")


def run_reports(root: Path) -> tuple[dict, HealthReport]:
    structure = structure_report(root)
    health = calculate_health(root, structure)
    write_structure_report(root, structure)
    write_health_json(root, health)
    write_checklist(root, structure, health)
    write_project_manager_audit(root, health)
    return structure, health


def safe_relative_input(root: Path, value: str) -> Path:
    cleaned = value.strip().replace("\\", os.sep).replace("/", os.sep)
    relative = Path(cleaned)
    candidate = relative if relative.is_absolute() else root / relative
    ensure_inside_root(root, candidate)
    return candidate


def add_folder(root: Path, value: str) -> None:
    path = safe_relative_input(root, value)
    path.mkdir(parents=True, exist_ok=True)
    ok(f"Folder added: {path}")
    structure, health = run_reports(root)
    print_structure_summary(structure)
    print_health_summary(health)


def add_file(root: Path, value: str) -> None:
    path = safe_relative_input(root, value)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        warn(f"File already exists: {path}")
    else:
        title = path.stem.replace("_", " ").replace("-", " ").title()
        path.write_text(f"# {title}\n\nDescribe this project item.\n", encoding="utf-8")
        ok(f"File added: {path}")
    structure, health = run_reports(root)
    print_structure_summary(structure)
    print_health_summary(health)


def snapshot(root: Path) -> tuple[tuple[str, int, int], ...]:
    entries: list[tuple[str, int, int]] = []
    if not root.exists():
        return tuple()

    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if any(part in IGNORED_NAMES for part in relative.parts):
            continue
        try:
            stat = path.stat()
            entries.append((normalize(relative), stat.st_mtime_ns, stat.st_size))
        except OSError:
            continue

    return tuple(sorted(entries))


def watch(root: Path, interval: float) -> None:
    heading("AGENTIC STUDIO WATCH MODE")
    info(f"Watching {root}")
    info("Press Ctrl+C to stop.")
    previous = snapshot(root)

    structure, health = run_reports(root)
    print_structure_summary(structure)
    print_health_summary(health)

    try:
        while True:
            time.sleep(interval)
            current = snapshot(root)
            if current != previous:
                info("Repository change detected. Running audit.")
                structure, health = run_reports(root)
                print_structure_summary(structure)
                print_health_summary(health)
                previous = current
    except KeyboardInterrupt:
        print()
        ok("Watch mode stopped.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create and manage the Agentic Studio Digital Twin repository."
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="create",
        choices=["create", "audit", "health", "watch", "add-file", "add-folder"],
        help="Action to perform. Default: create",
    )
    parser.add_argument(
        "item",
        nargs="?",
        help="Relative path used by add-file or add-folder.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_ROOT,
        help=f"Project root. Default: {DEFAULT_ROOT}",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace existing starter files during create.",
    )
    parser.add_argument(
        "--init-git",
        action="store_true",
        help="Initialize a Git repository after creating the structure.",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=3.0,
        help="Watch interval in seconds. Minimum: 1. Default: 3",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    root = args.root.expanduser()

    try:
        if args.command == "create":
            heading("AGENTIC STUDIO BOOTSTRAP VERSION 2")
            created, preserved = create_structure(root, overwrite=args.overwrite)
            ok(f"Created or updated {created} items.")
            info(f"Preserved {preserved} existing items.")

            if args.init_git:
                success, message = initialize_git(root)
                if success:
                    ok(message)
                else:
                    warn(message)

            structure, health = run_reports(root)
            print_structure_summary(structure)
            print_health_summary(health)
            print()
            ok(f"Checklist: {root / 'PROJECT_CHECKLIST.md'}")
            ok(f"Manager audit: {root / 'reports' / 'PROJECT_MANAGER_AUDIT.md'}")
            return 0

        if not root.exists():
            fail(f"Project root does not exist: {root}")
            fail("Run the create command first.")
            return 2

        if args.command == "audit":
            structure, health = run_reports(root)
            print_structure_summary(structure)
            print_health_summary(health)
            return 0 if structure["status"] == "PASS" else 1

        if args.command == "health":
            structure, health = run_reports(root)
            print_health_summary(health)
            print()
            info(f"Full audit: {root / 'reports' / 'PROJECT_MANAGER_AUDIT.md'}")
            return 0 if health.maturity_score >= 50 else 1

        if args.command == "watch":
            watch(root, max(args.interval, 1.0))
            return 0

        if args.command in {"add-file", "add-folder"}:
            if not args.item:
                parser.error(f"{args.command} requires a relative path.")
            if args.command == "add-file":
                add_file(root, args.item)
            else:
                add_folder(root, args.item)
            return 0

    except PermissionError as exc:
        fail(f"Permission denied: {exc}")
        return 3
    except ValueError as exc:
        fail(f"Invalid path: {exc}")
        return 4
    except OSError as exc:
        fail(f"File-system error: {exc}")
        return 5
    except subprocess.SubprocessError as exc:
        fail(f"Git command failed: {exc}")
        return 6
    except Exception as exc:
        fail(f"Unexpected error: {exc}")
        return 99

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
