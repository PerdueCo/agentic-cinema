from unittest.mock import patch, MagicMock
import pytest
import sys
from scripts.deploy_agent_engine import deploy, main, SecretRef

@patch("scripts.deploy_agent_engine.vertexai.init")
@patch("scripts.deploy_agent_engine.create_adk_app")
@patch("scripts.deploy_agent_engine.agent_engines.create")
def test_deploy_arguments(mock_create, mock_create_adk_app, mock_init):
    # Setup mock return values
    mock_app = MagicMock()
    mock_create_adk_app.return_value = mock_app

    mock_resource = MagicMock()
    mock_resource.name = "projects/mock-project/locations/us-central1/agentEngines/mock-engine"
    mock_create.return_value = mock_resource

    # Run deploy()
    res = deploy()

    # Verify vertexai.init was called correctly
    mock_init.assert_called_once_with(
        project="gen-lang-client-0908811561",
        location="us-central1",
        staging_bucket="gs://agentic-cinema-scene42-agent-engine-318775065448"
    )

    # Verify create_adk_app was called
    mock_create_adk_app.assert_called_once()

    # Verify agent_engines.create was called with the correct parameters
    mock_create.assert_called_once()
    kwargs = mock_create.call_args[1]

    assert kwargs["agent_engine"] == mock_app
    assert kwargs["display_name"] == "Scene 42 Production Decision Agent"
    assert kwargs["requirements"] == [
        "google-adk==2.7.1",
        "google-cloud-aiplatform[agent_engines,adk]==1.165.1",
        "google-genai==2.17.0",
        "parallel-web==1.2.0"
    ]
    assert kwargs["extra_packages"] == ["src"]

    # Verify env_vars
    env_vars = kwargs["env_vars"]
    assert env_vars["GOOGLE_GENAI_USE_VERTEXAI"] == "true"
    assert "GOOGLE_CLOUD_PROJECT" not in env_vars
    assert "GOOGLE_CLOUD_LOCATION" not in env_vars
    assert env_vars["SCENE42_MODEL_LOCATION"] == "global"
    assert env_vars["GEMINI_MODEL"] == "gemini-3.6-flash"

    # Verify SecretRef
    secret_ref = env_vars["PARALLEL_API_KEY"]
    assert isinstance(secret_ref, SecretRef)
    assert secret_ref.secret == "scene42-parallel-api-key"
    assert secret_ref.version == "2"

    # Verify instances and service account
    assert kwargs["service_account"] == "scene42-agent-engine@gen-lang-client-0908811561.iam.gserviceaccount.com"
    assert kwargs["min_instances"] == 0
    assert kwargs["max_instances"] == 1

    # Verify returned resource
    assert res == mock_resource


@patch("scripts.deploy_agent_engine.deploy")
def test_cli_no_argument_dry_run(mock_deploy):
    # Setup mock sys.argv to simulate running script with no arguments
    with patch.object(sys, "argv", ["deploy_agent_engine.py"]):
        main()

    # Verify deploy() is NOT called when --deploy is omitted
    mock_deploy.assert_not_called()


@patch("scripts.deploy_agent_engine.deploy")
def test_cli_deploy_flag(mock_deploy):
    # Setup mock deploy return value
    mock_resource = MagicMock()
    mock_resource.name = "projects/mock-project/locations/us-central1/agentEngines/mock-engine"
    mock_deploy.return_value = mock_resource

    # Setup mock sys.argv to simulate running script with --deploy
    with patch.object(sys, "argv", ["deploy_agent_engine.py", "--deploy"]):
        main()

    # Verify deploy() IS called
    mock_deploy.assert_called_once()
