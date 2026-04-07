variable "hcloud_token" {
  description = "Hetzner Cloud API token."
  type        = string
  sensitive   = true
}

variable "server_name" {
  description = "Hetzner server name."
  type        = string
  default     = "infra-main"
}

variable "server_image" {
  description = "Hetzner image name."
  type        = string
  default     = "ubuntu-24.04"
}

variable "server_type" {
  description = "Hetzner server type."
  type        = string
  default     = "cpx21"
}

variable "server_location" {
  description = "Hetzner location."
  type        = string
  default     = "fsn1"
}

variable "ssh_key_names" {
  description = "Hetzner SSH key names to inject into the server."
  type        = list(string)
}

variable "ssh_allowed_cidrs" {
  description = "CIDRs allowed to reach SSH."
  type        = list(string)
  default     = ["0.0.0.0/0", "::/0"]
}

variable "enable_public_http" {
  description = "Whether to open ports 80 and 443 in the Hetzner firewall."
  type        = bool
  default     = false
}

variable "labels" {
  description = "Labels applied to the server and firewall."
  type        = map(string)
  default = {
    project = "infra-macro-vps"
    env     = "production"
  }
}
