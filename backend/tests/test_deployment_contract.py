from pathlib import Path


def test_v22_dependency_layer_precedes_application_source() -> None:
    dockerfile = Path("Dockerfile").read_text(encoding="utf-8")
    assert dockerfile.index("pip install") < dockerfile.index("COPY app ./app")


def test_v22_ssh_deployment_allows_slow_first_build() -> None:
    workflow = Path("../.github/workflows/deploy.yml").read_text(encoding="utf-8")
    assert "command_timeout: 30m" in workflow


def test_v23_pip_downloads_survive_slow_or_interrupted_network() -> None:
    dockerfile = Path("Dockerfile").read_text(encoding="utf-8")
    assert "--mount=type=cache,target=/root/.cache/pip" in dockerfile
    assert "--default-timeout=120" in dockerfile
    assert "--retries 10" in dockerfile
    assert "--no-cache-dir" not in dockerfile


def test_v24_uploaded_images_bypass_frontend_static_regex() -> None:
    nginx = Path("../frontend/nginx.conf").read_text(encoding="utf-8")
    assert "location ^~ /uploads/" in nginx


def test_v25_production_site_has_favicon_and_legacy_fallback() -> None:
    index = Path("../frontend/index.html").read_text(encoding="utf-8")
    nginx = Path("../frontend/nginx.conf").read_text(encoding="utf-8")
    assert 'rel="icon" href="/favicon.svg"' in index
    assert Path("../frontend/public/favicon.svg").is_file()
    assert "location = /favicon.ico" in nginx
