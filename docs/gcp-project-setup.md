# GCP project setup (assignment)

One-time Google Cloud setup for the Encore car-insurance onboarding proxy and
Cloud Run deploy. Insait configuration stays manual; see `TODO.md`.

## Google One vs Google Cloud

**Google One Pro** (storage, consumer perks) is not the same product as **Google Cloud
billing**. You still sign in with the same personal `@gmail.com` account, but the
first time you use GCP you create a **Cloud Billing account** and attach a payment
method in the [billing console](https://console.cloud.google.com/billing). New GCP
accounts often get trial credit; this assignment’s Cloud Run usage is tiny if you
idle between demos. **Budget amount currency must match your billing account**
(check with `gcloud billing accounts describe BILLING_ID --format='value(currencyCode)'`).
Using `5USD` on an **ILS** account returns `INVALID_ARGUMENT`.

## Recommended shape

| Decision | Recommendation |
|----------|----------------|
| **Account** | Personal Google account with billing (not a locked-down work org if you need a **public** Cloud Run URL for Insait). |
| **Project** | Dedicated project, e.g. `onboarding-flow-YYMMDD`. |
| **Region** | `us-central1` (matches Terraform default and upstream webhook region). |
| **People** | You as **Owner** (or equivalent) — no extra users required for the assignment. |
| **CI service account** | Not required; deploy from your machine with ADC. |
| **Spend** | Optional **billing budget** alert (~$10/month); assignment traffic is tiny. |

## What Terraform creates (you do not hand-roll these)

- Enable APIs: Cloud Run, Artifact Registry, IAM, Cloud Resource Manager.
- Artifact Registry Docker repo `onboarding-flow`.
- Cloud Run runtime service account `onboarding-flow-run@…` with `roles/artifactregistry.reader`.
- Cloud Run v2 service (after you pass `container_image`).
- Optional `allUsers` → `roles/run.invoker` when `allow_unauthenticated = true` (default).

## Permissions you need on the project

For `terraform apply` using your user credentials (ADC), you need to be able to:

- Enable services (`serviceusage.services.enable`).
- Create service accounts and IAM bindings.
- Create Artifact Registry repositories and Cloud Run services.
- Set Cloud Run IAM (public invoker).

**Owner** on a new personal project is simplest. Minimum custom mix if you cannot use Owner:

| Role | Why |
|------|-----|
| `roles/editor` | Create most resources |
| `roles/serviceusage.serviceUsageAdmin` | Enable APIs |
| `roles/iam.serviceAccountAdmin` | Runtime service account |
| `roles/resourcemanager.projectIamAdmin` | `allUsers` invoker binding |
| `roles/run.admin` | Cloud Run service |
| `roles/artifactregistry.admin` | Docker repository |

On the **billing account**, you need **Billing Account User** to link the project.

## Org policies that block the assignment

- **Domain restricted sharing** or **public access prevention** can deny `allUsers` on Cloud Run.
  Symptom: Terraform fails on `google_cloud_run_v2_service_iam_member.public_invoker`.
  Fix: use a personal project, or set `allow_unauthenticated = false` and call Cloud Run with auth (harder for Insait).

## Limits already encoded in Terraform

- Cloud Run scale to zero; `max_instances` in `terraform.tfvars` (default variable is 3; this
  project uses `1` for a tighter cap)
- Container: 1 CPU, 512Mi memory
- Upstream HTTP timeout 5s (app env)

Default GCP quotas are sufficient; no quota increase requests are expected.

## Billing budget (optional)

Create in the [console](https://console.cloud.google.com/billing/budgets) scoped to your
project. Budget **currency must match** the billing account (e.g. `20ILS`, not `5USD`, when
`currencyCode` is `ILS`).

## Deploy after the project exists

Follow [`infra/README.md`](../infra/README.md): foundation Terraform (if not applied yet),
image build/push, full `terraform apply` with `container_image`, smoke `POST /vehicle-info`,
then configure Insait with `terraform output -raw vehicle_info_url`.
