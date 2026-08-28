# Agentic Studio Digital Twin — Functional Human-in-the-Loop Demo

This repository is a working vertical slice based on the supplied UI concept. It demonstrates the complete Scene 42 weather story:

**Detect & Ingest → Physics Analysis → Safety Assessment → Producer Recommendation → Human Approval → Digital Twin Update**

The demo is intentionally designed to work **without any API keys**, so you can see the application first. Google Gemini and Parallel Search are optional integrations you can enable afterward.

## What works now

- Landing page
- Demo authentication page
- Executive dashboard
- Scene 42 weather event
- Physics and safety assessments
- Explainable producer recommendation
- Human Approve / Reject decision
- Digital Twin state update after approval
- Event history in the FastAPI backend
- Responsive desktop/mobile layout
- Optional Parallel Search endpoint
- Environment placeholders for Gemini

## Architecture

```text
React + TypeScript (Vite)
        |
        v
FastAPI REST API
        |
        +--> Research Agent ---- Parallel Search API (optional)
        +--> Physics Agent ----- deterministic demo model
        +--> Safety Agent ------ risk rules
        +--> Producer Agent ---- recommendation
        +--> Human Approval ---- APPROVE / REJECT
        |
        v
Digital Twin State + Event History

Next integration layer:
Google GenAI SDK / Gemini
Google Cloud Agent Builder / ADK
Cloud Run
PostgreSQL / Cloud SQL
Pub/Sub event bus
```

## Run on Windows PowerShell

Open **PowerShell window #1**:

```powershell
cd "C:\Users\cash america\Documents\Projects\Agentic-Cinema"

# Copy this demo folder into your repo first, then:
cd .\agentic-studio-functional-demo\backend

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
python -m uvicorn app.main:app --reload --port 8000
```

You should see FastAPI running at `http://127.0.0.1:8000`.

Open **PowerShell window #2**:

```powershell
cd "C:\Users\cash america\Documents\Projects\Agentic-Cinema\agentic-studio-functional-demo\frontend"
npm install
npm run dev
```

Open the URL Vite displays, normally `http://localhost:5173`.

## Demo sequence for judges

1. Click **Launch Platform**.
2. Click **Sign In** on the demo authentication screen.
3. On the Executive Dashboard, click **Run / Refresh Analysis**.
4. Walk left-to-right through Research → Physics → Safety → Producer.
5. Point out that the Producer Agent recommends a move but **does not change the production**.
6. Click **Approve**.
7. Show the Digital Twin card change from Exterior to **Stage B**, with schedule, budget, equipment, crew, and safety state updated.
8. Click **Reset Demo** to repeat the story.

## Enable Parallel Search later

Parallel's official Python package is `parallel-web`. Add your key to `backend/.env`:

```env
PARALLEL_API_KEY=your_key_here
ALLOW_LIVE_RESEARCH=true
```

The backend already includes `POST /api/research` as the integration seam.

## Enable Gemini next

Google's current Python SDK package is `google-genai`. To enable Gemini via Vertex AI, configure Application Default Credentials (ADC) by setting:

~~~env
GOOGLE_CLOUD_PROJECT=your_project_id
GOOGLE_CLOUD_LOCATION=global
GEMINI_MODEL=gemini-3.6-flash
~~~

Make sure you have authenticated your environment:

~~~bash
gcloud auth application-default login
~~~

The next development step is to move the Producer recommendation explanation and selected agent reasoning into a Gemini service while keeping physics/safety thresholds deterministic and auditable.

## Important engineering choice

For this demonstration, **AI recommends; humans authorize; the Digital Twin records the outcome**. Safety-critical calculations should remain deterministic/rule-based or physics-model-based, with Gemini used to explain, synthesize, and reason over those outputs rather than invent safety thresholds.
