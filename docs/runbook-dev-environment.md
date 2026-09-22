# Dev environment runbook (Fedora 44 WSL on Windows ARM64)

Target: develop and test the onboarding-flow proxy on **Linux aarch64** in WSL,
build **OCI images** for Cloud Run, and keep the app loop on **uv + Python 3.14**.

Last validated against: Fedora Linux 44 (WSL), `aarch64`, Docker/Moby 29.7.2,
Podman 5.8.7.

---

## 1. Environment audit (what was wrong)

| Check | Healthy signal | Your machine (before fix) |
|-------|----------------|---------------------------|
| App tests | `./scripts/check.sh` passes | OK (45 passed) |
| `docker` daemon | `docker info` (Server section) | Running, but **permission denied** in shells not in `docker` group session |
| `docker buildx` | `docker buildx version` | **Missing plugin** (`unknown command: docker buildx`) |
| `podman` | `podman info` | **Missing `crun`** OCI runtime |
| systemd | `systemctl is-system-running` | **degraded** (common on WSL; docker still ran) |

**Cleanup applied (packages):**

```bash
sudo dnf install -y docker-buildx crun
```

**Still required (session):** after being added to group `docker`, **log out of WSL
and open a new terminal** (or run `newgrp docker`) so `docker info` works without
`sudo`.

---

## 2. Choose one primary container workflow

Both engines work after the package install. Pick **one** daily driver to avoid
split-brain.

| | **Moby + BuildKit (recommended here)** | **Rootless Podman** |
|--|----------------------------------------|---------------------|
| **When** | Dockerfile uses BuildKit; matches many CI examples | Fedora-native, no root daemon |
| **Build** | `DOCKER_BUILDKIT=1 docker build …` | `podman build …` |
| **Run** | `docker run …` | `podman run …` |
| **Gotcha on WSL** | Must be in `docker` group + new login | WSL rootless mount warning (often OK for smoke tests) |

Integration tests under `tests/integration/` invoke **`docker build`** with
`DOCKER_BUILDKIT=1` via `./scripts/check-image.sh`. Default `./scripts/check.sh`
does not run them.

---

## 3. One-time setup (Fedora 44 WSL)

### 3.1 WSL + systemd (optional but helps)

In **Windows** `%USERPROFILE%\.wslconfig` or distro `/etc/wsl.conf`:

```ini
[boot]
systemd=true
```

Restart WSL from PowerShell: `wsl --shutdown`, then reopen the distro.

### 3.2 Container packages

```bash
sudo dnf install -y \
  moby-engine docker-cli docker-buildx containerd \
  podman crun containers-common
```

Enable and start Docker (if using Moby):

```bash
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"
```

**New WSL session** (close all terminals, reopen), then verify:

```bash
docker info          # must show Server, not permission denied
docker buildx version
podman info          # must not complain about crun
```

### 3.3 Python + uv (app loop)

```bash
sudo dnf install -y python3.14 python3.14-devel  # or use uv-managed Python only
curl -LsSf https://astral.sh/uv/install.sh | sh   # if uv not installed
```

Project:

```bash
cd ~/dev/labs/onboarding-flow
uv sync
./scripts/check.sh
```

---

## 4. Daily commands

| Task | Command |
|------|---------|
| Lint / types / unit tests | `./scripts/check.sh` (as **your user**, not `sudo`) |
| Run API locally | `uv run granian --interface asgi onboarding_flow.app:app --host 0.0.0.0 --port 8080` |
| Image smoke (build + health) | `./scripts/check-image.sh --container-force-build -v` |
| Manual image build (BuildKit) | `./scripts/docker-build.sh onboarding-flow:test linux/arm64` |
| **Cloud Run push** | `./scripts/docker-build.sh --push …/onboarding-flow:latest` or `cloudbuild.yaml` (see `infra/README.md`) |
| Rootless build (alt.) | `podman build -t onboarding-flow:test .` |

---

## 5. Verification checklist

Run after setup or OS updates:

```bash
uname -m                    # aarch64
uv --version && python3 --version
./scripts/check.sh

docker info | head -20
docker buildx version
DOCKER_BUILDKIT=1 docker build -t onboarding-flow:verify .
docker run --rm -p 8080:8080 onboarding-flow:verify &
curl -sf http://127.0.0.1:8080/health
docker stop $(docker ps -q --filter ancestor=onboarding-flow:verify)
```

Optional Podman parity:

```bash
podman build -t onboarding-flow:verify .
podman run --rm -p 8080:8080 onboarding-flow:verify
```

---

## 6. Troubleshooting

### `permission denied` on `/var/run/docker.sock`

- Confirm group: `groups` includes `docker`.
- **New login** after `usermod -aG docker` (WSL: close all distro windows).
- Temporary: `sg docker -c "docker info"`.

### `unknown command: docker buildx`

```bash
sudo dnf install -y docker-buildx
ls /usr/libexec/docker/cli-plugins/docker-buildx
```

### `default OCI runtime "crun" not found` (Podman)

```bash
sudo dnf install -y crun
```

### Build fails: `--mount requires BuildKit`

```bash
export DOCKER_BUILDKIT=1
docker buildx version
```

Do not use the legacy builder; install `docker-buildx` instead.

### `./scripts/check.sh: uv: command not found` (after `sudo`)

Do **not** run the check script with `sudo`. Root’s `PATH` does not include
`~/.local/bin` where `uv` is installed. Use:

```bash
bash scripts/check.sh
# or
./scripts/check.sh
```

### systemd `degraded` on WSL

Often harmless if `docker.service` is **active (running)**. Fix only if services
fail to start; prefer `systemd=true` in WSL config.

---

## 7. Optional cleanup (reduce confusion)

Only if you commit to **one** engine:

```bash
# Docker-only (keep Podman packages if you use toolbox)
# sudo dnf remove podman   # optional

# Podman-only
# sudo systemctl disable --now docker docker.socket
# sudo dnf remove moby-engine docker-cli docker-buildx
```

Default recommendation: **keep both installed**, use **Moby + buildx** for this
repo’s smoke test and **Podman** for ad-hoc rootless experiments.

---

## 8. Cloud Run (Terraform)

Deploy via [`infra/README.md`](../infra/README.md) (Terraform, not ad-hoc `gcloud run deploy`).

**gcloud on Fedora 44 WSL (aarch64):** use the official `google-cloud-cli-linux-arm.tar.gz`
install under `$HOME/google-cloud-sdk` (see [`infra/README.md`](../infra/README.md)); avoid
Windows scoop `gcloud` shims on WSL `PATH`.

Configure `infra/terraform/terraform.tfvars`, then follow the three deploy phases in the infra
README (foundation → image push → Cloud Run apply).

Insait flow configuration remains manual; see `TODO.md` section 4.
