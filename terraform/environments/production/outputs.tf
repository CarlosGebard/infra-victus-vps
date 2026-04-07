output "server_name" {
  description = "Created server name."
  value       = module.single_node.server_name
}

output "server_ipv4" {
  description = "Primary public IPv4."
  value       = module.single_node.server_ipv4
}

output "firewall_name" {
  description = "Attached firewall name."
  value       = module.single_node.firewall_name
}
