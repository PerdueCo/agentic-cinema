# Environment Setup

## Requirements

- Python 3.10+
- Node.js 20+ (for the React/TypeScript frontend, once implemented)
- A Google Cloud project with the Gemini API enabled
- A Parallel account and API key ([parallel.ai](https://parallel.ai))
- Git

Docker is not currently required — the backend and frontend don't have
containerized setups yet. This section will be updated once those exist.

## Python version management

This repo pins its Python version in `.python-version` (currently `3.10.4`).
If you have multiple projects needing different Python versions, use
[pyenv](https://github.com/pyenv/pyenv) (macOS/Linux) or
[pyenv-win](https://github.com/pyenv-win/pyenv-win) (Windows) instead of
installing Python directly — it lets versions coexist on your machine
without upgrading or removing whatever you already have installed.

```bash
pyenv install 3.10.4   # only needed once, adds this version alongside others
cd agentic-cinema       # pyenv reads .python-version and switches automatically
python --version        # confirm it shows 3.10.4
```

Then build the venv as normal (below) — it will be created from the pinned
version automatically.

## Install

```bash
git clone https://github.com/PerdueCo/agentic-cinema.git
cd agentic-cinema
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
```

## Environment variables

Copy the template and fill in your own keys — never commit `.env`:

```bash
cp .env.example .env
```

| Variable | Where to get it |
|---|---|
| `GOOGLE_CLOUD_PROJECT` | Your GCP project ID |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to a GCP service account key, if using Application Default Credentials instead of an API key |
| `GEMINI_API_KEY` | [Google AI Studio](https://aistudio.google.com/apikey) |
| `PARALLEL_API_KEY` | [Parallel dashboard](https://platform.parallel.ai) |

## Verify it works

```bash
python -m src.agents.research_agent
```

If your keys are set correctly, this prints a `ResearchFinding` with a real
summary and source URL. If you don't have keys yet, you can still confirm
the code itself is sound by running the mocked test suite instead:

```bash
pytest tests/ -q
```

## Frontend

`src/frontend/` is a placeholder — no `package.json` exists yet. This
section will be filled in once the React/TypeScript app is scaffolded.