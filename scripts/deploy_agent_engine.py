import sys
import argparse
import vertexai
from vertexai import agent_engines
from google.cloud.aiplatform_v1.types.env_var import SecretRef
from src.entry_agent import create_adk_app

PROJECT_ID = "gen-lang-client-0908811561"
DEPLOYMENT_LOCATION = "us-central1"
MODEL_LOCATION = "global"
STAGING_BUCKET = "gs://agentic-cinema-scene42-agent-engine-318775065448"
RUNTIME_SERVICE_ACCOUNT = "scene42-agent-engine@gen-lang-client-0908811561.iam.gserviceaccount.com"
PARALLEL_SECRET_NAME = "scene42-parallel-api-key"
PARALLEL_SECRET_VERSION = "1"

def deploy():
    """Initializes Vertex AI and deploys the Agent Engine resource."""
    vertexai.init(
        project=PROJECT_ID,
        location=DEPLOYMENT_LOCATION,
        staging_bucket=STAGING_BUCKET
    )

    app = create_adk_app()

    resource = agent_engines.create(
        agent_engine=app,
        display_name="Scene 42 Production Decision Agent",
        description="The production decision-making agent for Scene 42.",
        requirements=[
            "google-adk==2.7.1",
            "google-cloud-aiplatform[agent_engines,adk]==1.165.1",
            "google-genai==2.17.0",
            "parallel-web==1.2.0"
        ],
        extra_packages=["src"],
        env_vars={
            "GOOGLE_GENAI_USE_VERTEXAI": "true",
            "GOOGLE_CLOUD_PROJECT": PROJECT_ID,
            "GOOGLE_CLOUD_LOCATION": MODEL_LOCATION,
            "GEMINI_MODEL": "gemini-3.6-flash",
            "PARALLEL_API_KEY": SecretRef(
                secret=PARALLEL_SECRET_NAME,
                version=PARALLEL_SECRET_VERSION
            )
        },
        service_account=RUNTIME_SERVICE_ACCOUNT,
        min_instances=0,
        max_instances=1
    )
    return resource

def main():
    parser = argparse.ArgumentParser(description="Deploy Agent Engine")
    parser.add_argument("--deploy", action="store_true", help="Perform the actual deployment")
    args = parser.parse_args()

    if args.deploy:
        print("Starting actual deployment of Agent Engine...")
        resource = deploy()
        resource_name = getattr(resource, 'name', str(resource))
        print(f"Deployment successful. Resource name: {resource_name}")
    else:
        print("=== DRY RUN SUMMARY ===")
        print(f"Project ID: {PROJECT_ID}")
        print(f"Deployment Region: {DEPLOYMENT_LOCATION}")
        print(f"Staging Bucket: {STAGING_BUCKET}")
        print(f"Service Account: {RUNTIME_SERVICE_ACCOUNT}")
        print(f"Secret Name: {PARALLEL_SECRET_NAME}")
        print(f"Secret Version: {PARALLEL_SECRET_VERSION}")
        print("=======================")
        print("Note: Actual deployment did not run. Use --deploy to deploy.")

if __name__ == "__main__":
    main()
