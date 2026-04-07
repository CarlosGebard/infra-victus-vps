output "server_name" {
  description = "Server name."
  value       = hcloud_server.this.name
}

output "server_ipv4" {
  description = "Primary public IPv4."
  value       = hcloud_server.this.ipv4_address
}

output "firewall_name" {
  description = "Firewall name."
  value       = hcloud_firewall.this.name
}
