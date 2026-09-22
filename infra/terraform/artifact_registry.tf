resource "google_artifact_registry_repository" "app" {
  location      = var.region
  repository_id = var.artifact_registry_repository_id
  description   = "Docker images for onboarding-flow vehicle proxy"
  format        = "DOCKER"

  depends_on = [google_project_service.required]
}
