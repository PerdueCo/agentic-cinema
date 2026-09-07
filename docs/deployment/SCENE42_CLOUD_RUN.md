# Scene 42 Cloud Run deployment proposal

This runbook deploys two independent Cloud Run services in `us-central1`:

- `scene42-api`: FastAPI backend that calls the existing managed Agent Engine.
- `scene42-web`: React static frontend that calls `scene42-api`.

The services are intentionally separate. The frontend receives only the public
backend URL. The Parallel API key remains a Secret Manager reference on the
existing Agent Engine and is never injected into the frontend or Cloud Run API.

## Fixed resource configuration

| Setting | Value |
| --- | --- |
| Project | `gen-lang-client-0908811561` |
| Region | `us-central1` |
| Runtime service account | `scene42-agent-engine@gen-lang-client-0908811561.iam.gserviceaccount.com` |
| Agent Engine resource | `projects/318775065448/locations/us-central1/reasoningEngines/8164504406155329536` |
| Backend service | `scene42-api` |
| Frontend service | `scene42-web` |
| Artifact Registry repository | `scene42-containers` |

## Required APIs

Before deployment, explicitly authorize enabling:

- `run.googleapis.com`
- `artifactregistry.googleapis.com`
- `cloudbuild.googleapis.com`

Vertex AI, Secret Manager, and Cloud Storage are already present. API enabling
and deployment are separate approval gates.

## Runtime environment

The backend service uses these non-secret environment variables:

```text
ALLOW_LIVE_AGENTS=true
ALLOW_LIVE_RESEARCH=false
GOOGLE_CLOUD_PROJECT=gen-lang-client-0908811561
SCENE42_AGENT_ENGINE_LOCATION=us-central1
SCENE42_AGENT_ENGINE_RESOURCE_NAME=projects/318775065448/locations/us-central1/reasoningEngines/8164504406155329536
CORS_ALLOWED_ORIGINS=https://FRONTEND_CLOUD_RUN_HOST
```

`ALLOW_LIVE_RESEARCH` remains false in FastAPI because Parallel executes inside
the managed Agent Engine. Do not set `PARALLEL_API_KEY` on either Cloud Run
service. The frontend image is built with:

```text
VITE_API_BASE=https://BACKEND_CLOUD_RUN_HOST
```

This Vite value is compiled into the static browser bundle and is not a secret.

## Deployment order

1. Enable the three required APIs after explicit approval.
2. Create the regional Docker repository `scene42-containers`.
3. Build the backend from the repository root using
   `agentic-studio-functional-demo/backend/Dockerfile`.
4. Deploy `scene42-api` with one worker, the existing runtime service account,
   `min-instances=0`, `max-instances=1`, concurrency `1`, and the non-secret
   variables above.
5. Record the backend HTTPS URL.
6. Build the frontend from `agentic-studio-functional-demo/frontend`, passing
   the backend URL as `VITE_API_BASE`.
7. Deploy `scene42-web` publicly with `min-instances=0`.
8. Record the frontend HTTPS URL.
9. Update only `CORS_ALLOWED_ORIGINS` on `scene42-api` to the exact frontend
   origin, without a trailing slash.

Both services require public HTTPS access for a judge to use the application.
The current prototype has no user authentication, so this is controlled demo
exposure rather than a production security model. Keep the backend at one
instance, monitor usage, and remove public access after judging if it is no
longer required.

## Proposed build and deployment commands

Run these only after separate approval. Values shown here contain no secrets.

```powershell
$project = "gen-lang-client-0908811561"
$region = "us-central1"
$repository = "scene42-containers"
$registry = "$region-docker.pkg.dev/$project/$repository"
$runtimeServiceAccount = `
    "scene42-agent-engine@$project.iam.gserviceaccount.com"
$agentEngine = `
    "projects/318775065448/locations/us-central1/reasoningEngines/8164504406155329536"
$backendImage = "$registry/scene42-api:COMMIT_SHA"
$frontendImage = "$registry/scene42-web:COMMIT_SHA"
```

Enable APIs and create the repository only after their own approval gate:

```powershell
gcloud services enable `
    run.googleapis.com `
    artifactregistry.googleapis.com `
    cloudbuild.googleapis.com `
    --project=$project

gcloud artifacts repositories create $repository `
    --project=$project `
    --location=$region `
    --repository-format=docker `
    --description="Scene 42 Cloud Run images"
```

Build and deploy the backend first:

```powershell
gcloud builds submit . `
    --project=$project `
    --region=$region `
    --config=deploy/cloudbuild.backend.yaml `
    --substitutions="_IMAGE=$backendImage"

gcloud run deploy scene42-api `
    --project=$project `
    --region=$region `
    --image=$backendImage `
    --service-account=$runtimeServiceAccount `
    --allow-unauthenticated `
    --min-instances=0 `
    --max-instances=1 `
    --concurrency=1 `
    --timeout=180s `
    --set-env-vars="ALLOW_LIVE_AGENTS=true,ALLOW_LIVE_RESEARCH=false,GOOGLE_CLOUD_PROJECT=$project,SCENE42_AGENT_ENGINE_LOCATION=$region,SCENE42_AGENT_ENGINE_RESOURCE_NAME=$agentEngine"
```

Read the backend URL, build the frontend with that URL, and deploy it:

```powershell
$backendUrl = gcloud run services describe scene42-api `
    --project=$project `
    --region=$region `
    --format="value(status.url)"

gcloud builds submit . `
    --project=$project `
    --region=$region `
    --config=deploy/cloudbuild.frontend.yaml `
    --substitutions="_IMAGE=$frontendImage,_VITE_API_BASE=$backendUrl"

gcloud run deploy scene42-web `
    --project=$project `
    --region=$region `
    --image=$frontendImage `
    --allow-unauthenticated `
    --min-instances=0 `
    --max-instances=2 `
    --port=8080

$frontendUrl = gcloud run services describe scene42-web `
    --project=$project `
    --region=$region `
    --format="value(status.url)"

gcloud run services update scene42-api `
    --project=$project `
    --region=$region `
    --update-env-vars="CORS_ALLOWED_ORIGINS=$frontendUrl"
```

Before running Cloud Build, confirm that its build identity can write to the
single Artifact Registry repository. Before deploying the API, confirm the
deploying account can act as the runtime service account. Grant only the narrow
missing role at the relevant resource after a separate IAM review.

The backend must remain at one instance because workflow state is currently
stored in process memory. Horizontal scaling would split dashboard and approval
state across instances. This is suitable for the controlled demonstration, not
for a multi-user production system.

## Container build contexts

Build the backend with the repository root as its context because it imports the
top-level `src` package:

```text
docker build -f agentic-studio-functional-demo/backend/Dockerfile .
```

Build the frontend with its own directory as context:

```text
docker build --build-arg VITE_API_BASE=https://BACKEND_CLOUD_RUN_HOST agentic-studio-functional-demo/frontend
```

The root `.dockerignore` excludes local environments, reports, generated files,
secrets, and `digital-twin-trailer-parallel` from the backend build context.

## Health and readiness checks

- Backend container/Cloud Run probe: `GET /api/health`; expect HTTP 200 and
  `status: ok`, `mode: live`, and `agent_engine_configured: true`.
- Frontend container/Cloud Run probe: `GET /healthz`; expect HTTP 200 and `ok`.
- Browser initial state: load the frontend and confirm `AWAITING_ANALYSIS`
  behavior before invoking any paid workflow.

## Controlled verification

Perform verification as separate gates:

1. Public health checks only.
2. Initial-state desktop and mobile browser checks.
3. One explicitly authorized live Scene 42 analysis.
4. Confirm Research, Scheduling, Budget, and Producer results render.
5. Confirm the recommendation remains pending until a human decision.
6. Approve or reject only with separate authorization, then verify Digital Twin
   and event history behavior.
7. Confirm Cloud Run and Agent Engine logs contain no secret values.

## Rollback

Cloud Run retains revisions. If verification fails:

1. Stop live workflow testing.
2. Route 100% traffic back to the last verified backend or frontend revision.
3. If no verified public revision exists, remove public traffic rather than
   changing the Agent Engine.
4. Do not delete the Agent Engine, its staging bucket, service account, or
   Parallel secret.
5. Retain the failed revision and logs for diagnosis; do not overwrite evidence.

Repository rollback is independent: revert the deployment-configuration commit
with a new commit. Do not rewrite shared Git history or force-push.
