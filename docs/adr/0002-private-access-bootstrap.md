# ADR 0002: Private-Access Bootstrap Model

## Status

Accepted

## Context

The initial deployment target is a single Hetzner VPS accessed through the local SSH alias `hetzner-main`.

At this stage, the operator does not want public application ingress. The system still needs an internal reverse proxy so that services can share a single entry point and preserve a clean routing model for later public exposure.

## Decision

The bootstrap deployment mode is private-only:

- Hetzner firewall allows SSH ingress by default.
- HTTP and HTTPS firewall access remain disabled by default.
- The Compose stack binds NGINX to `127.0.0.1:8080` on the host.
- Operators access the stack through SSH tunnels.
- CouchDB, SeaweedFS, Infisical, PostgreSQL, and Redis remain internal-only on the Docker backend network.

## Consequences

Positive:

- Reduced external attack surface during bootstrap
- No accidental exposure of stateful internal services
- Easy transition to public ingress later by changing Terraform and NGINX settings intentionally

Tradeoffs:

- Browser access requires SSH tunneling
- TLS termination and public domain routing are deferred to a later milestone
