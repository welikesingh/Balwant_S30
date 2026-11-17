
variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "sent-score-api"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "dev"
}

variable "external_port" {
  description = "Port exposed on the host machine"
  type        = number
  default     = 8080

  validation {
    condition = (
      var.external_port >= 1024 &&
      var.external_port <= 65535
    )
    error_message = "Use a port between 1024 and 65535."
  }
}

variable "internal_port" {
  description = "FastAPI port inside the container"
  type        = number
  default     = 8000
}

variable "image_tag" {
  description = "Docker image version"
  type        = string
  default     = "v3"
}
