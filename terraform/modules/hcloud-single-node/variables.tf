variable "name" {
  description = "Server name."
  type        = string
}

variable "image" {
  description = "Server image."
  type        = string
}

variable "server_type" {
  description = "Hetzner server type."
  type        = string
}

variable "location" {
  description = "Hetzner location."
  type        = string
}

variable "ssh_key_names" {
  description = "SSH key names registered in Hetzner."
  type        = list(string)
}

variable "ssh_allowed_cidrs" {
  description = "CIDRs allowed to reach SSH."
  type        = list(string)
}

variable "enable_public_http" {
  description = "Whether to allow 80 and 443 in the firewall."
  type        = bool
}

variable "labels" {
  description = "Labels to apply to created resources."
  type        = map(string)
}
