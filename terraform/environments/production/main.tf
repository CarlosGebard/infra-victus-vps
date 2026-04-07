provider "hcloud" {
  token = var.hcloud_token
}

module "single_node" {
  source = "../../modules/hcloud-single-node"

  name               = var.server_name
  image              = var.server_image
  server_type        = var.server_type
  location           = var.server_location
  ssh_key_names      = var.ssh_key_names
  ssh_allowed_cidrs  = var.ssh_allowed_cidrs
  enable_public_http = var.enable_public_http
  labels             = var.labels
}
