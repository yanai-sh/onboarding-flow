output "project_id" {
  value = var.project_id
}

output "region" {
  value = var.region
}

output "artifact_registry_repository" {
  value = google_artifact_registry_repository.app.name
}

output "artifact_registry_host" {
  value = "${var.region}-docker.pkg.dev"
}

output "image_repository_uri" {
  description = "Prefix for docker tag (append /onboarding-flow:TAG)."
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.app.repository_id}"
}

output "cloud_run_url" {
  value = google_cloud_run_v2_service.app.uri
}

output "vehicle_info_url" {
  value = "${google_cloud_run_v2_service.app.uri}/vehicle-info"
}

output "health_url" {
  value = "${google_cloud_run_v2_service.app.uri}/health"
}
