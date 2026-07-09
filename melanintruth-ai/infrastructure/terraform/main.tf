terraform { required_version = ">= 1.6.0" }
variable "environment" { type = string }
output "deployment_note" { value = "Provision PostgreSQL, Redis, object storage with encryption, KMS, and audit log sink." }
