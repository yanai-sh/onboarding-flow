resource "google_cloud_run_v2_service" "app" {
  name                = var.service_name
  location            = var.region
  ingress             = "INGRESS_TRAFFIC_ALL"
  deletion_protection = false

  template {
    service_account = google_service_account.run.email

    scaling {
      min_instance_count = 0
      max_instance_count = var.max_instances
    }

    containers {
      image = var.container_image

      ports {
        container_port = 8080
      }

      env {
        name  = "UPSTREAM_URL"
        value = var.upstream_url
      }

      env {
        name  = "UPSTREAM_TIMEOUT_SECONDS"
        value = tostring(var.upstream_timeout_seconds)
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
        cpu_idle = true
      }
    }
  }

  depends_on = [
    google_project_service.required,
    google_artifact_registry_repository.app,
    google_project_iam_member.run_ar_reader,
  ]

  lifecycle {
    ignore_changes = [
      client,
      client_version,
    ]
  }
}
