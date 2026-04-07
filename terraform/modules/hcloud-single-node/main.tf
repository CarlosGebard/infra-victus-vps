resource "hcloud_server" "this" {
  name        = var.name
  image       = var.image
  server_type = var.server_type
  location    = var.location
  ssh_keys    = var.ssh_key_names
  labels      = var.labels

  public_net {
    ipv4_enabled = true
    ipv6_enabled = false
  }
}

locals {
  ingress_rules = concat(
    [
      {
        direction  = "in"
        protocol   = "tcp"
        port       = "22"
        source_ips = var.ssh_allowed_cidrs
      }
    ],
    var.enable_public_http ? [
      {
        direction  = "in"
        protocol   = "tcp"
        port       = "80"
        source_ips = ["0.0.0.0/0", "::/0"]
      },
      {
        direction  = "in"
        protocol   = "tcp"
        port       = "443"
        source_ips = ["0.0.0.0/0", "::/0"]
      }
    ] : []
  )
}

resource "hcloud_firewall" "this" {
  name   = "${var.name}-firewall"
  labels = var.labels

  dynamic "rule" {
    for_each = local.ingress_rules

    content {
      direction  = rule.value.direction
      protocol   = rule.value.protocol
      port       = rule.value.port
      source_ips = rule.value.source_ips
    }
  }
}

resource "hcloud_firewall_attachment" "this" {
  firewall_id = hcloud_firewall.this.id
  server_ids  = [hcloud_server.this.id]
}
