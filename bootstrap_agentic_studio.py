#!/usr/bin/env python3
"""
bootstrap_agentic_studio.py

Creates and audits the Agentic Studio Digital Twin GitHub repository structure.

PowerShell examples:
    python .\bootstrap_agentic_studio.py create
    python .\bootstrap_agentic_studio.py audit
    python .\bootstrap_agentic_studio.py watch
    python .\bootstrap_agentic_studio.py add-file docs\vision\ProjectCharter.md
    python .\bootstrap_agentic_studio.py add-folder docs\security

Default project location:
    C:\Users\cash america\Documents\Projects\Agentic-Cinema

The script:
1. Creates the approved folders and starter files.
2. Generates PROJECT_CHECKLIST.md.
3. Reports missing, present, and unexpected items.
4. Writes reports\structure_audit.json.
5. Can watch the repository and rerun the audit when files change.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Iterable

DEFAULT_ROOT = Path(r"C:\Users\cash america\Documents\Projects\Agentic-Cinema")

# Files created with useful starter content.
STARTER_FILES: dict[str, str] = {
    "README.md": """# Agentic Studio Digital Twin

An AI-powered Digital Twin of a movie production where autonomous AI agents
collaborate to plan, monitor, and optimize filmmaking from script to release.

## Start Here

- [Vision](docs/vision/Vision.md)
- [Roadmap](docs/roadmap/Production_Roadmap.md)
- [Enterprise Architecture](docs/architecture/EnterpriseArchitecture.md)
- [Digital Twin Overview](docs/digital-twin/DigitalTwinOverview.md)
- [Developer Onboarding](docs/onboarding/NewDeveloperGuide.md)
- [Mentor Guide](docs/onboarding/MentorGuide.md)
- [Project Checklist](PROJECT_CHECKLIST.md)

## Demonstration Story

Weather changes → Digital Twin updates → Schedule and budget impacts are
calculated → AI agents recommend an action → A human approves the decision.
""",
    "docs/vision/Vision.md": """# Vision

Create a living digital movie studio—not merely a chatbot—where AI agents
collaborate through a shared Digital Twin from script to release.
""",
    "docs/vision/Mission.md": """# Mission

Help filmmaking teams make faster, safer, explainable, and better-informed
production decisions while preserving human approval and creative control.
""",
    "docs/vision/Production_Guide.md": """# Production Guide

Describe the movie-production lifecycle represented by the platform.
""",
    "docs/roadmap/Production_Roadmap.md": """# Production Roadmap

- [ ] ACT I — The Vision
- [ ] ACT II — Pre-Production
- [ ] ACT III — Lights, Camera, Code
- [ ] ACT IV — Post-Production
- [ ] ACT V — The Premiere
- [ ] ACT VI — The Franchise
""",
    "docs/architecture/EnterpriseArchitecture.md": "# Enterprise Architecture\n\nDescribe the full platform and external systems.\n",
    "docs/architecture/AIAgentArchitecture.md": "# AI Agent Architecture\n\nDescribe agent roles, orchestration, memory, tools, and approvals.\n",
    "docs/architecture/DigitalTwinArchitecture.md": "# Digital Twin Architecture\n\nDescribe identities, metadata, relationships, state, history, events, observations, and recommendations.\n",
    "docs/architecture/DataFlowArchitecture.md": "# Data Flow Architecture\n\nDescribe event and data movement through the studio.\n",
    "docs/architecture/CloudArchitecture.md": "# Cloud Architecture\n\nDescribe Google Cloud, Gemini, Agent Builder, IBM Bob, and optional Confluent components.\n",
    "docs/digital-twin/DigitalTwinOverview.md": """# Digital Twin Overview

The Digital Twin models movies, scripts, scenes, shots, actors, crew, locations,
equipment, lighting, audio, props, budgets, schedules, weather, production
status, editing, visual effects, marketing, and distribution.
""",
    "docs/digital-twin/MovieModel.md": "# Movie Model\n\nDefine the movie, script, scene, and shot entities.\n",
    "docs/digital-twin/ProductionObjects.md": "# Production Objects\n\nDefine crew, cast, locations, equipment, props, schedules, budgets, and status.\n",
    "docs/digital-twin/AIObservationModel.md": "# AI Observation Model\n\nDefine AI observations, confidence, evidence, recommendations, and human decisions.\n",
    "docs/ai-agents/DirectorAgent.md": "# Director Agent\n\nResponsibilities, inputs, tools, outputs, and approval boundaries.\n",
    "docs/ai-agents/ProducerAgent.md": "# Producer Agent\n\nResponsibilities, inputs, tools, outputs, and approval boundaries.\n",
    "docs/ai-agents/SchedulingAgent.md": "# Scheduling Agent\n\nResponsibilities, inputs, tools, outputs, and approval boundaries.\n",
    "docs/ai-agents/BudgetAgent.md": "# Budget Agent\n\nResponsibilities, inputs, tools, outputs, and approval boundaries.\n",
    "docs/ai-agents/MarketingAgent.md": "# Marketing Agent\n\nResponsibilities, inputs, tools, outputs, and approval boundaries.\n",
    "docs/engineering/EngineeringPrompt.md": "# Master Engineering Prompt\n\nPlace the approved multidisciplinary engineering prompt here.\n",
    "docs/engineering/CodingStandards.md": "# Coding Standards\n\nDocument naming, formatting, testing, security, and review rules.\n",
    "docs/engineering/DevelopmentGuide.md": "# Development Guide\n\nDocument the local development workflow.\n",
    "docs/onboarding/NewDeveloperGuide.md": "# New Developer Guide\n\nExplain setup, architecture, first task, testing, and pull requests.\n",
    "docs/onboarding/MentorGuide.md": "# Mentor Guide\n\nExplain project context, feedback areas, meeting format, and boundaries.\n",
    "docs/onboarding/EnvironmentSetup.md": "# Environment Setup\n\nDocument Python, Node.js, Docker, Google Cloud, IBM Bob, and environment variables.\n",
    "docs/api/API.md": "# API\n\nDocument endpoints, requests, responses, errors, and authentication.\n",
    "docs/api/Events.md": "# Events\n\nDocument production events and agent-triggering rules.\n",
    "docs/deployment/LocalSetup.md": "# Local Setup\n\nDocument local startup and shutdown instructions.\n",
    "docs/deployment/GoogleCloud.md": "# Google Cloud Deployment\n\nDocument cloud resources and deployment steps.\n",
    "docs/deployment/CI-CD.md": "# CI/CD\n\nDocument automated build, test, security, and deployment workflows.\n",
    "docs/wiki/FAQ.md": "# Frequently Asked Questions\n",
    "docs/wiki/Glossary.md": "# Glossary\n\nDefine Agentic AI, Digital Twin, production objects, events, and human-in-the-loop.\n",
    "docs/wiki/LessonsLearned.md": "# Lessons Learned\n\nCapture technical, product, teamwork, and hackathon lessons.\n",
    "templates/ArchitectureTemplate.md": "# Architecture Title\n\n## Purpose\n\n## Components\n\n## Data Flow\n\n## Security\n\n## Decisions\n",
    "templates/AgentTemplate.md": "# Agent Name\n\n## Purpose\n\n## Inputs\n\n## Tools\n\n## Outputs\n\n## Approval Boundaries\n",
    "templates/DesignTemplate.md": "# Design Title\n\n## User\n\n## Problem\n\n## Flow\n\n## Acceptance Criteria\n",
    "templates/StoryTemplate.md": "# User Story\n\nAs a...\n\nI want...\n\nSo that...\n\n## Acceptance Criteria\n",
    "templates/MeetingNotes.md": "# Meeting Notes\n\n**Date:**\n\n**Attendees:**\n\n## Decisions\n\n## Actions\n",
    "src/frontend/.gitkeep": "",
    "src/backend/.gitkeep": "",
    "src/agents/.gitkeep": "",
    "src/digital_twin/.gitkeep": "",
    "src/services/.gitkeep": "",
    "src/shared/.gitkeep": "",
    "tests/.gitkeep": "",
    "scripts/.gitkeep": "",
    "examples/sample-script/.gitkeep": "",
    "examples/sample-production/.gitkeep": "",
    "examples/sample-weather/.gitkeep": "",
    "examples/sample-budget/.gitkeep": "",
    "examples/sample-agents/.gitkeep": "",
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
    "presentations/GoogleHackathon/.gitkeep": "",
    "presentations/MentorReview/.gitkeep": "",
    "presentations/InvestorPitch/.gitkeep": "",
    "presentations/DemoDay/.gitkeep": "",
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

# IDE / OS
.vscode/
.idea/
.DS_Store
Thumbs.db

# Reports generated by local audit
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
    ".github/workflows",
    ".github/ISSUE_TEMPLATE",
    "reports",
]

# These are allowed to exist without being marked as unexpected.
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
}


def normalized(path: Path) -> str:
    return path.as_posix().lstrip("./")


def expected_paths() -> set[str]:
    return set(REQUIRED_FOLDERS) | set(STARTER_FILES) | GENERATED_FILES


def ensure_inside_root(root: Path, candidate: Path) -> None:
    try:
        candidate.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError("The requested path must remain inside the project root.") from exc


def create_structure(root: Path, overwrite: bool = False) -> tuple[int, int]:
    root.mkdir(parents=True, exist_ok=True)
    created = 0
    skipped = 0

    for folder in REQUIRED_FOLDERS:
        path = root / folder
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            created += 1

    for relative, content in STARTER_FILES.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and not overwrite:
            skipped += 1
            continue
        path.write_text(content, encoding="utf-8")
        created += 1

    return created, skipped


def list_actual_paths(root: Path) -> set[str]:
    actual: set[str] = set()
    if not root.exists():
        return actual

    for path in root.rglob("*"):
        relative_parts = path.relative_to(root).parts
        if any(part in IGNORED_NAMES for part in relative_parts):
            continue
        actual.add(normalized(path.relative_to(root)))
    return actual


def find_unexpected(root: Path, expected: set[str]) -> list[str]:
    unexpected: list[str] = []

    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if any(part in IGNORED_NAMES for part in relative.parts):
            continue

        rel = normalized(relative)
        if rel in expected:
            continue

        # Do not flag parent folders that naturally contain expected children.
        prefix = rel.rstrip("/") + "/"
        if path.is_dir() and any(item.startswith(prefix) for item in expected):
            continue

        unexpected.append(rel + ("/" if path.is_dir() else ""))

    return sorted(unexpected, key=str.lower)


def audit_structure(root: Path) -> dict:
    expected = expected_paths()
    actual = list_actual_paths(root)

    required_folder_set = set(REQUIRED_FOLDERS)
    required_file_set = set(STARTER_FILES)

    missing_folders = sorted(
        [item for item in required_folder_set if not (root / item).is_dir()],
        key=str.lower,
    )
    missing_files = sorted(
        [item for item in required_file_set if not (root / item).is_file()],
        key=str.lower,
    )
    present_folders = sorted(required_folder_set - set(missing_folders), key=str.lower)
    present_files = sorted(required_file_set - set(missing_files), key=str.lower)
    unexpected = find_unexpected(root, expected)

    total_required = len(required_folder_set) + len(required_file_set)
    total_present = len(present_folders) + len(present_files)
    completion = round((total_present / total_required) * 100, 1) if total_required else 100.0

    return {
        "project_root": str(root),
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "completion_percent": completion,
        "required_count": total_required,
        "present_count": total_present,
        "missing_folders": missing_folders,
        "missing_files": missing_files,
        "present_folders": present_folders,
        "present_files": present_files,
        "unexpected_items": unexpected,
        "actual_item_count": len(actual),
        "status": "PASS" if not missing_folders and not missing_files else "ACTION REQUIRED",
    }


def checkbox(exists: bool) -> str:
    return "x" if exists else " "


def group_items(items: Iterable[str]) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {}
    for item in sorted(items, key=str.lower):
        top = item.split("/", 1)[0]
        groups.setdefault(top, []).append(item)
    return groups


def write_checklist(root: Path, report: dict) -> Path:
    checklist_path = root / "PROJECT_CHECKLIST.md"
    lines = [
        "# Agentic Studio Repository Check-Off Sheet",
        "",
        f"**Last audit:** {report['generated_at']}",
        f"**Project root:** `{report['project_root']}`",
        f"**Status:** **{report['status']}**",
        f"**Completion:** **{report['completion_percent']}%** "
        f"({report['present_count']} of {report['required_count']} required items)",
        "",
        "Run the audit again:",
        "",
        "```powershell",
        r"python .\bootstrap_agentic_studio.py audit",
        "```",
        "",
        "## Required Folders",
        "",
    ]

    for group, items in group_items(REQUIRED_FOLDERS).items():
        lines.append(f"### `{group}`")
        lines.append("")
        for item in items:
            exists = (root / item).is_dir()
            lines.append(f"- [{checkbox(exists)}] `{item}/`")
        lines.append("")

    lines.extend(["## Required Files", ""])
    for group, items in group_items(STARTER_FILES.keys()).items():
        lines.append(f"### `{group}`")
        lines.append("")
        for item in items:
            exists = (root / item).is_file()
            lines.append(f"- [{checkbox(exists)}] `{item}`")
        lines.append("")

    lines.extend(["## Missing Items Requiring Action", ""])
    missing = report["missing_folders"] + report["missing_files"]
    if missing:
        for item in missing:
            lines.append(f"- [ ] `{item}`")
    else:
        lines.append("- [x] No required folders or files are missing.")

    lines.extend(["", "## Added or Unexpected Items", ""])
    if report["unexpected_items"]:
        lines.append(
            "These items are not automatically wrong. Review them and decide whether "
            "they should be accepted into the official structure."
        )
        lines.append("")
        for item in report["unexpected_items"]:
            lines.append(f"- [ ] Review `{item}`")
    else:
        lines.append("- [x] No unexpected items found.")

    lines.extend(
        [
            "",
            "## Agent Review Questions",
            "",
            "- [ ] Does each new folder have a clear purpose?",
            "- [ ] Is new documentation linked from `README.md` or a relevant index?",
            "- [ ] Are secrets stored only in environment variables and never committed?",
            "- [ ] Does each AI agent document its inputs, tools, outputs, and approval boundaries?",
            "- [ ] Does each architecture change update the appropriate diagram?",
            "- [ ] Does each feature include tests or documented acceptance criteria?",
            "- [ ] Is the weather-impact demonstration still runnable?",
            "- [ ] Are mentor materials separated from official builder work?",
            "- [ ] Are Google Cloud, Gemini, IBM Bob, and Confluent usage clearly documented?",
            "- [ ] Is the project scope realistic for the hackathon deadline?",
            "",
            "## Recommended Next Action",
            "",
        ]
    )

    if report["missing_folders"] or report["missing_files"]:
        lines.append("Create or restore the missing required items listed above.")
    elif report["unexpected_items"]:
        lines.append("Review the added items and either keep, document, move, or remove them.")
    else:
        lines.append("The approved repository structure is complete. Continue feature development.")

    lines.append("")
    checklist_path.write_text("\n".join(lines), encoding="utf-8")
    return checklist_path


def write_json_report(root: Path, report: dict) -> Path:
    report_path = root / "reports" / "structure_audit.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report_path


def print_report(report: dict) -> None:
    print("\n" + "=" * 72)
    print("AGENTIC STUDIO STRUCTURE AUDIT")
    print("=" * 72)
    print(f"Root:       {report['project_root']}")
    print(f"Status:     {report['status']}")
    print(f"Completion: {report['completion_percent']}%")
    print(f"Required:   {report['present_count']} / {report['required_count']} present")

    if report["missing_folders"]:
        print("\nMISSING FOLDERS")
        for item in report["missing_folders"]:
            print(f"  [MISSING] {item}/")

    if report["missing_files"]:
        print("\nMISSING FILES")
        for item in report["missing_files"]:
            print(f"  [MISSING] {item}")

    if report["unexpected_items"]:
        print("\nADDED OR UNEXPECTED ITEMS")
        for item in report["unexpected_items"]:
            print(f"  [REVIEW]  {item}")

    if not report["missing_folders"] and not report["missing_files"]:
        print("\n[OK] All required folders and files are present.")

    print("\nChecklist: PROJECT_CHECKLIST.md")
    print("JSON log:  reports\\structure_audit.json")
    print("=" * 72 + "\n")


def run_audit(root: Path) -> dict:
    report = audit_structure(root)
    write_checklist(root, report)
    write_json_report(root, report)
    print_report(report)
    return report


def safe_relative_input(root: Path, value: str) -> Path:
    cleaned = value.strip().replace("\\", os.sep).replace("/", os.sep)
    relative = Path(cleaned)
    if relative.is_absolute():
        candidate = relative
    else:
        candidate = root / relative
    ensure_inside_root(root, candidate)
    return candidate


def add_folder(root: Path, value: str) -> None:
    path = safe_relative_input(root, value)
    path.mkdir(parents=True, exist_ok=True)
    print(f"[ADDED] Folder: {path}")
    run_audit(root)


def add_file(root: Path, value: str) -> None:
    path = safe_relative_input(root, value)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        title = path.stem.replace("_", " ").replace("-", " ").title()
        path.write_text(f"# {title}\n\nDescribe this project item.\n", encoding="utf-8")
        print(f"[ADDED] File: {path}")
    else:
        print(f"[EXISTS] File: {path}")
    run_audit(root)


def snapshot(root: Path) -> tuple[tuple[str, int, int], ...]:
    entries: list[tuple[str, int, int]] = []
    if not root.exists():
        return tuple()

    for path in root.rglob("*"):
        rel = path.relative_to(root)
        if any(part in IGNORED_NAMES for part in rel.parts):
            continue
        try:
            stat = path.stat()
            entries.append((normalized(rel), stat.st_mtime_ns, stat.st_size))
        except OSError:
            continue
    return tuple(sorted(entries))


def watch(root: Path, interval: float) -> None:
    print(f"Watching: {root}")
    print("Press Ctrl+C to stop.\n")
    previous = snapshot(root)
    run_audit(root)

    try:
        while True:
            time.sleep(interval)
            current = snapshot(root)
            if current != previous:
                print("\n[CHANGE DETECTED] Running repository audit...")
                run_audit(root)
                previous = current
    except KeyboardInterrupt:
        print("\nWatcher stopped.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create and audit the Agentic Studio Digital Twin repository."
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="create",
        choices=["create", "audit", "watch", "add-file", "add-folder"],
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
        "--interval",
        type=float,
        default=3.0,
        help="Watch interval in seconds. Default: 3",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    root = args.root.expanduser()

    try:
        if args.command == "create":
            created, skipped = create_structure(root, overwrite=args.overwrite)
            print(f"[CREATE COMPLETE] Created or updated: {created}; preserved: {skipped}")
            run_audit(root)
            return 0

        if not root.exists():
            print(f"[ERROR] Project root does not exist: {root}", file=sys.stderr)
            print("Run the create command first.", file=sys.stderr)
            return 2

        if args.command == "audit":
            report = run_audit(root)
            return 0 if report["status"] == "PASS" else 1

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
        print(f"[PERMISSION ERROR] {exc}", file=sys.stderr)
        return 3
    except ValueError as exc:
        print(f"[INVALID PATH] {exc}", file=sys.stderr)
        return 4
    except OSError as exc:
        print(f"[FILE SYSTEM ERROR] {exc}", file=sys.stderr)
        return 5

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
