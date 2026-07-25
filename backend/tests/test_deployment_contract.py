from pathlib import Path


def test_v22_dependency_layer_precedes_application_source() -> None:
    dockerfile = Path("Dockerfile").read_text(encoding="utf-8")
    assert dockerfile.index("pip install") < dockerfile.index("COPY app ./app")


def test_v22_ssh_deployment_allows_slow_first_build() -> None:
    workflow = Path("../.github/workflows/deploy.yml").read_text(encoding="utf-8")
    assert "command_timeout: 30m" in workflow
