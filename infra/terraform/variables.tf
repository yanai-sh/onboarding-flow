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

variable "image_tag" {
  description = "Image tag pushed by cloudbuild.yaml (git short SHA). Pass per deploy: -var image_tag=$(git rev-parse --short HEAD)."
  type        = string

  validation {
    condition     = var.image_tag != "" && var.image_tag != "latest"
    error_message = "image_tag must be an immutable tag such as the git short SHA; Cloud Run only rolls a new revision when the image reference changes."
  }
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

variable "log_level" {
  description = "Application and Granian worker log level passed as LOG_LEVEL."
  type        = string
  default     = "INFO"

  validation {
    condition     = contains(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], var.log_level)
    error_message = "log_level must be one of DEBUG, INFO, WARNING, ERROR, CRITICAL."
  }
}

variable "granian_workers_kill_timeout" {
  description = "Grace given to in-flight requests and lifespan shutdown on SIGTERM. Keep under Cloud Run's 10s termination grace."
  type        = string
  default     = "8s"
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
