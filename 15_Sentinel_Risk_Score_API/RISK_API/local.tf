locals {
  container_name = "${var.project_name}-${var.environment}"
  image_name     = "${var.project_name}:${var.image_tag}"

  application_url = "http://localhost:${var.external_port}"

  common_labels = {
    project     = var.project_name
    environment = var.environment
    managed_by  = "terraform"
  }
}