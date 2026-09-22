# GCP infrastructure (Terraform)

Terraform stack for Part A: enable APIs, Artifact Registry, Cloud Run v2, runtime service
account, and public `run.invoker` for Insait (configurable).

| Path | Role |
|------|------|
| [`terraform/`](terraform/) | All infrastructure definitions |
| [`terraform/terraform.tfvars.example`](terraform/terraform.tfvars.example) | Copy to `terraform.tfvars` |
| [`terraform/.terraform-version`](terraform/.terraform-version) | Terraform pin (tfenv / asdf / mise) |

One-time project/billing notes: [`docs/gcp-project-setup.md`](../docs/gcp-project-setup.md).

## Prerequisites

Install tools with **your** package manager or version manager; this repo only declares infra
in Terraform.

| Tool | Pin / notes |
|------|-------------|
| Google Cloud CLI | Auth + `gcloud auth configure-docker` |
| Terraform | ≥ 1.5 — see [`.terraform-version`](terraform/.terraform-version) |
| Docker + BuildKit | Image build/push — see [`docs/runbook-dev-environment.md`](../docs/runbook-dev-environment.md) |

### Fedora 44 WSL (aarch64 — official tarball)

COPR often returns **404 for `fedora-44`**; on this machine use the **linux-arm**
tarball (native aarch64, not the Windows scoop shims on `PATH`):

```bash
cd /tmp
curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-linux-arm.tar.gz
tar -xf google-cloud-cli-linux-arm.tar.gz
./google-cloud-sdk/install.sh
# install to $HOME/google-cloud-sdk; ensure ~/.bashrc sources path.bash.inc from $HOME, not /tmp
gcloud components install docker-credential-gcr
gcloud --version
```

Optional COPR on older Fedora releases: `sudo dnf copr enable @google-cloud-sdk/google-cloud-sdk`
then `sudo dnf install google-cloud-cli`.

Terraform on Fedora: `sudo dnf install terraform` when available, or
[HashiCorp install docs](https://developer.hashicorp.com/terraform/install#linux).

### GCP auth (once per machine)

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud auth application-default login
```

Application Default Credentials are what the Terraform Google provider uses.

## Configuration

```bash
cp infra/terraform/terraform.tfvars.example infra/terraform/terraform.tfvars
# set project_id (region defaults to us-central1 in variables.tf)
```

## Deploy

### 1. Init and foundation (first time)

```bash
cd infra/terraform
terraform init
```

Apply APIs, Artifact Registry, and the Cloud Run runtime service account before the first
image push:

```bash
terraform apply -auto-approve \
  -target='google_project_service.required["run.googleapis.com"]' \
  -target='google_project_service.required["artifactregistry.googleapis.com"]' \
  -target='google_project_service.required["iam.googleapis.com"]' \
  -target='google_project_service.required["cloudresourcemanager.googleapis.com"]' \
  -target=google_artifact_registry_repository.app \
  -target=google_service_account.run \
  -target=google_project_iam_member.run_ar_reader
```

### 2. Build and push image

Set `container_image` in `terraform.tfvars` to the URI you will push (example below).
From the **repository root**, build and push that same tag (no shell exports required):

The Dockerfile requires **BuildKit** (`--mount`). Use **`docker buildx`**, not legacy
`docker build`. `gcloud builds submit --tag` alone uses the legacy builder and will fail.

**Cloud Build (recommended on aarch64 WSL):** [`cloudbuild.yaml`](../cloudbuild.yaml) runs
`docker buildx build` on amd64 workers:

```bash
# From repository root; _IMAGE must match container_image in terraform.tfvars
gcloud config set project your-project-id
gcloud services enable cloudbuild.googleapis.com compute.googleapis.com --quiet
gcloud builds submit --region=us-central1 --config=cloudbuild.yaml \
  --substitutions=_IMAGE=us-central1-docker.pkg.dev/your-project-id/onboarding-flow/onboarding-flow:latest .
```

After the first successful build, if push to Artifact Registry fails, grant the Cloud Build
service account `roles/artifactregistry.writer` on the project (see troubleshooting).

**Local buildx (push):** requires `docker-buildx` and, on ARM64, QEMU for `linux/amd64`:

```bash
sudo dnf install -y docker-buildx qemu-user-static
docker run --rm --privileged tonistiigi/binfmt --install all
gcloud auth configure-docker us-central1-docker.pkg.dev
./scripts/docker-build.sh --push \
  us-central1-docker.pkg.dev/your-project-id/onboarding-flow/onboarding-flow:latest
```

Use your real `project_id` from `terraform.tfvars` in the paths above.

### 3. Cloud Run + public invoker

`container_image` is read from `terraform.tfvars`:

```bash
cd infra/terraform
terraform apply -auto-approve
```

### Smoke test

```bash
curl -sS "$(terraform output -raw vehicle_info_url)" \
  -H 'Content-Type: application/json' \
  -d '{"license_plate":"12345678"}'
```

Use `terraform output -raw vehicle_info_url` as the Insait API node URL.

## Troubleshooting

- **`allUsers` invoker denied:** Set `allow_unauthenticated = false` in `terraform.tfvars` or use a
  personal GCP project without that org constraint.
- **WSL + Windows `gcloud` shims:** Use the Fedora COPR CLI inside WSL instead of Scoop shims on
  UNC paths.
- **`manifest type ... must support amd64/linux`:** Image was ARM-only. Rebuild for amd64, push,
  then `terraform apply`.
- **`--mount option requires BuildKit` / legacy builder deprecated:** Use
  `gcloud builds submit --config=cloudbuild.yaml` or `./scripts/docker-build.sh`, not plain
  `docker build` / `gcloud builds submit --tag`.
- **`exec format error` during amd64 build on aarch64:** Install `qemu-user-static` + binfmt, or
  use Cloud Build with `cloudbuild.yaml`.
- **`gcloud builds submit` PERMISSION_DENIED** (even as Owner): enable **`compute.googleapis.com`**
  (Cloud Build depends on it), use `--region=us-central1`, open
  [Cloud Build](https://console.cloud.google.com/cloud-build) once to accept terms, then retry.
  Do **not** use `sudo gcloud` (wrong PATH/credentials).
