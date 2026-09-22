"""Fixtures and CLI options for Docker image smoke tests."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from tests.shared import (
    DEFAULT_CONTAINER_IMAGE,
    DOCKER_BUILD_ENV,
    container_image_exists,
    docker_buildkit_available,
    docker_daemon_available,
)


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--container-image",
        action="store",
        default=DEFAULT_CONTAINER_IMAGE,
        help=f"Image tag for container smoke tests (default: {DEFAULT_CONTAINER_IMAGE}).",
    )
    parser.addoption(
        "--container-force-build",
        action="store_true",
        default=False,
        help="Rebuild the container image even if the tag already exists.",
    )


@pytest.fixture(scope="session")
def container_image_tag(pytestconfig: pytest.Config) -> str:
    return pytestconfig.getoption("--container-image", default=DEFAULT_CONTAINER_IMAGE)


@pytest.fixture(scope="module")
def built_image(pytestconfig: pytest.Config, container_image_tag: str) -> str:
    if not docker_daemon_available():
        pytest.skip("Docker daemon is not reachable (docker info failed).")
    if not docker_buildkit_available():
        pytest.skip(
            "BuildKit is required for this Dockerfile. Install docker-buildx "
            "(see docs/runbook-dev-environment.md)."
        )

    force_build = pytestconfig.getoption("--container-force-build", default=False)
    if force_build or not container_image_exists(container_image_tag):
        root = Path(__file__).resolve().parent.parent.parent
        completed = subprocess.run(
            [
                "docker",
                "buildx",
                "build",
                "--load",
                "-t",
                container_image_tag,
                str(root),
            ],
            capture_output=True,
            text=True,
            timeout=600,
            check=False,
            env={**os.environ, **DOCKER_BUILD_ENV},
        )
        if completed.returncode != 0:
            msg = f"docker buildx build failed:\n{completed.stderr}\n{completed.stdout}"
            pytest.fail(msg)
    return container_image_tag
