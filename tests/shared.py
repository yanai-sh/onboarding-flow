"""Test-only helpers and literals shared across pytest modules."""

from __future__ import annotations

import os
import shutil
import subprocess

from onboarding_flow.schemas import VehicleData

ASSIGNMENT_SAMPLE_VEHICLE = VehicleData(
    license_plate="12345678",
    manufacturer="Toyota",
    model="Corolla",
    year=2020,
    color="White",
)

DEFAULT_CONTAINER_IMAGE = "onboarding-flow:test"

# BuildKit is required for Dockerfile cache/bind mounts (not the legacy builder).
DOCKER_BUILD_ENV: dict[str, str] = {
    "DOCKER_BUILDKIT": "1",
    "COMPOSE_DOCKER_CLI_BUILD": "1",
}


def docker_daemon_available() -> bool:
    if shutil.which("docker") is None:
        return False
    try:
        completed = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=5,
            check=False,
            env={**os.environ, **DOCKER_BUILD_ENV},
        )
    except OSError, subprocess.TimeoutExpired:
        return False
    return completed.returncode == 0


def docker_buildkit_available() -> bool:
    """True when buildx/BuildKit tooling is present (project standard)."""
    if not docker_daemon_available():
        return False
    completed = subprocess.run(
        ["docker", "buildx", "version"],
        capture_output=True,
        timeout=5,
        check=False,
        env={**os.environ, **DOCKER_BUILD_ENV},
    )
    return completed.returncode == 0


def container_image_exists(tag: str) -> bool:
    if not docker_daemon_available():
        return False
    completed = subprocess.run(
        ["docker", "image", "inspect", tag],
        capture_output=True,
        timeout=10,
        check=False,
    )
    return completed.returncode == 0
