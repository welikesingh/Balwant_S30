
output "container_name" {
  description = "Created Docker container"
  value       = docker_container.fastapi.name
}

output "container_id" {
  description = "Docker container ID"
  value       = docker_container.fastapi.id
}

output "docker_image" {
  description = "Built Docker image"
  value       = local.image_name
}

output "api_url" {
  description = "FastAPI base URL"
  value       = local.application_url
}

output "swagger_url" {
  description = "Interactive API documentation"
  value       = "${local.application_url}/docs"
}

output "health_url" {
  description = "Application health endpoint"
  value       = "${local.application_url}/health"
}
