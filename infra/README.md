# GCP deploy (Terraform + Cloud Build)

[`terraform/`](terraform/) owns the required APIs, the Artifact Registry repository, the
Cloud Run v2 service (1 CPU, 512Mi, scale to zero, capped by `max_instances`), its runtime
service account (Artifact Registry reader), and the public `run.invoker` binding Insait needs
(`allow_unauthenticated`). [`cloudbuild.yaml`](../cloudbuild.yaml) builds the amd64 image;
Terraform deploys it by git short SHA, so every deploy rolls a new revision.

## Prerequisites

- A GCP project with billing linked and Owner on it (or editor, serviceusage.serviceUsageAdmin,
  iam.serviceAccountAdmin, resourcemanager.projectIamAdmin, run.admin, artifactregistry.admin).
- Google Cloud CLI and Terraform >= 1.5 ([`.terraform-version`](terraform/.terraform-version)).
- On Linux aarch64 (for example Fedora in WSL on Windows ARM64), install gcloud from the
  `google-cloud-cli-linux-arm.tar.gz` archive, not Windows gcloud shims on the WSL `PATH`.
  Cloud Build builds amd64 remotely, so no local QEMU is needed.

## One-time bootstrap

```bash
gcloud auth login
gcloud auth application-default login   # credentials for the Terraform provider
gcloud config set project YOUR_PROJECT_ID
gcloud services enable cloudbuild.googleapis.com compute.googleapis.com

cp infra/terraform/terraform.tfvars.example infra/terraform/terraform.tfvars   # set project_id
terraform -chdir=infra/terraform init
# The APIs and the Artifact Registry repository must exist before the first push.
# image_tag is a required variable; this targeted apply does not use it.
terraform -chdir=infra/terraform apply \
  -target=google_artifact_registry_repository.app -var image_tag=bootstrap
```

## Build and deploy

Commit first: Cloud Build uploads the working tree, and the tag should name what was built.

```bash
TAG="$(git rev-parse --short HEAD)"
gcloud builds submit --region=us-central1 --config=cloudbuild.yaml --substitutions=_TAG="$TAG" .
terraform -chdir=infra/terraform apply -var image_tag="$TAG"
```

The Dockerfile needs BuildKit (`RUN --mount`), so both build paths use `docker buildx`;
legacy `docker build` and `gcloud builds submit --tag` fail. Local alternative (needs
`gcloud auth configure-docker us-central1-docker.pkg.dev`, plus QEMU binfmt on aarch64):

```bash
scripts/docker-build.sh --push \
  "us-central1-docker.pkg.dev/YOUR_PROJECT_ID/onboarding-flow/onboarding-flow:$TAG"
```

## Verify

```bash
URL="$(terraform -chdir=infra/terraform output -raw cloud_run_url)"
curl -fsS "$URL/health"   # {"status":"ok"}
curl -sS "$URL/vehicle-info" -H 'Content-Type: application/json' \
  -d '{"license_plate":"12345678"}'   # "success":true with the (Hebrew) vehicle fields
terraform -chdir=infra/terraform output image   # deployed image tag
```

The current deployment is <https://onboarding-flow-2q2x6qga6a-uc.a.run.app>. The Insait API
node uses `terraform -chdir=infra/terraform output -raw vehicle_info_url`.

## Rollback

Every pushed SHA stays in Artifact Registry; redeploy an earlier one:

```bash
gcloud artifacts docker tags list \
  us-central1-docker.pkg.dev/YOUR_PROJECT_ID/onboarding-flow/onboarding-flow
terraform -chdir=infra/terraform apply -var image_tag=PREVIOUS_SHA
```

## Teardown

```bash
terraform -chdir=infra/terraform destroy -var image_tag=unused
```

This deletes the service, the repository with its images, and the service account; APIs stay
enabled. The `YOUR_PROJECT_ID_cloudbuild` source bucket is not Terraform-managed; delete it,
or the whole project with `gcloud projects delete YOUR_PROJECT_ID`.

## Troubleshooting

- **`allUsers` invoker denied** (org policy such as domain-restricted sharing): use a personal
  project, or set `allow_unauthenticated = false` (Insait would then need to authenticate).
- **`gcloud builds submit` PERMISSION_DENIED**: confirm `compute.googleapis.com` is enabled,
  pass `--region=us-central1`, and open the Cloud Build console once to accept its terms. If
  the push fails, grant the build service account `roles/artifactregistry.writer`.
- **`manifest type ... must support amd64/linux`**: the image was built for arm64. Rebuild
  for `linux/amd64` (the default in `cloudbuild.yaml` and `scripts/docker-build.sh`).
- **Changing `region`**: also pass `_REGION=<region>` to `gcloud builds submit`.
