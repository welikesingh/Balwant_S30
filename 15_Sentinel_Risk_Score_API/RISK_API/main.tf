
resource "docker_container" "fastapi" {
  name  = local.container_name
  image = local.image_name

  ports {
    internal = var.internal_port
    external = var.external_port
    ip       = "127.0.0.1"
  }

  restart = "unless-stopped"

  labels {
    label = "project"
    value = local.common_labels.project
  }

  labels {
    label = "environment"
    value = local.common_labels.environment
  }

  labels {
    label = "managed_by"
    value = local.common_labels.managed_by
  }
}
