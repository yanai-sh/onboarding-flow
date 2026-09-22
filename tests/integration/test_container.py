"""Docker image smoke test: build OCI image and verify /health on PORT."""

import json
import subprocess
import time

import httpx
import pytest

pytestmark = pytest.mark.container


def test_container_serves_health_on_port_8080(built_image: str) -> None:
    run = subprocess.run(
        ["docker", "run", "-d", "-p", "0:8080", built_image],
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
    )
    container_id = run.stdout.strip()
    port = (
        subprocess.run(
            ["docker", "port", container_id, "8080"],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
        .stdout.strip()
        .rsplit(":", maxsplit=1)[-1]
    )
    health_url = f"http://127.0.0.1:{port}/health"
    try:
        deadline = time.monotonic() + 30
        last_error: Exception | None = None
        while time.monotonic() < deadline:
            try:
                response = httpx.get(health_url, timeout=2)
                if response.status_code == 200 and response.json() == {"status": "ok"}:
                    return
            except (httpx.HTTPError, json.JSONDecodeError, TypeError, ValueError) as exc:
                last_error = exc
            time.sleep(0.5)
        msg = f"Container health check failed: {last_error}"
        raise AssertionError(msg)
    finally:
        subprocess.run(
            ["docker", "rm", "-f", container_id],
            check=False,
            capture_output=True,
        )
