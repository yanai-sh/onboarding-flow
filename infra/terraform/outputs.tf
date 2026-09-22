output "cloud_run_url" {
  value = google_cloud_run_v2_service.app.uri
}

output "vehicle_info_url" {
  description = "URL for the Insait API node."
  value       = "${google_cloud_run_v2_service.app.uri}/vehicle-info"
}

output "image" {
  description = "Image reference of the deployed revision."
  value       = google_cloud_run_v2_service.app.template[0].containers[0].image
}
