variable "project_id" {
  description = "GCP project ID (must exist and have billing enabled)."
  type        = string
}

variable "region" {
  description = "Primary region for Artifact Registry and Cloud Run."
  type        = string
  default     = "us-central1"
}

variable "service_name" {
  description = "Cloud Run service name (public URL path segment)."
  type        = string
  default     = "onboarding-flow"
}

variable "artifact_registry_repository_id" {
  description = "Docker Artifact Registry repository ID."
  type        = string
  default     = "onboarding-flow"
}

variable "container_image" {
  description = "Full image URI (region-docker.pkg.dev/PROJECT/REPO/onboarding-flow:TAG). Set via -var at apply time."
  type        = string
  default     = "us-docker.pkg.dev/cloudrun/container/hello"
}

variable "upstream_url" {
  description = "Encore vehicle-info upstream URL for the proxy."
  type        = string
  default     = "https://insurance-webhook-945894769129.us-central1.run.app/vehicle-info"
}

variable "upstream_timeout_seconds" {
  description = "Upstream HTTP timeout passed to the app as UPSTREAM_TIMEOUT_SECONDS."
  type        = number
  default     = 5
}

variable "allow_unauthenticated" {
  description = "Grant roles/run.invoker to allUsers so Insait can call POST /vehicle-info."
  type        = bool
  default     = true
}

variable "max_instances" {
  description = "Cloud Run max scale (assignment-scale traffic)."
  type        = number
  default     = 3
}
