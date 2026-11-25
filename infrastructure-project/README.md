# Workplace infrastructure on Ubuntu Server

I built a workplace Ubuntu Server environment to run a TAK server for ATAK and WinTAK clients alongside self-hosted tools. I started Dockge with Docker Compose, then managed the other services through Dockge. The environment included Starlink connectivity, a Cisco router, firewall services, network-attached storage (NAS), and Tailscale with MagicDNS for named access to resources.

## What this project shows

| Area | Tools and experience |
| --- | --- |
| Server and containers | Ubuntu Server, Docker Compose, Dockge |
| Applications | TAK for ATAK/WinTAK, Gitea, Pi-hole, Stirling PDF, Homarr |
| Security tools | Trivy, CrowdSec, Wazuh, Nessus |
| Connectivity and storage | Starlink, Cisco router, firewall services, NAS, Tailscale, MagicDNS |

This was workplace infrastructure, not a home lab. The public documentation is a high-level account, not an export: it contains no original configuration, addresses, certificates, credentials, or data. It does not claim measured impact or security outcomes.

## Explore the project

- [Architecture and boundaries](architecture.md) — workplace capability map and how it differs from the example.
- [Operations](operations.md) — sample setup instructions and suggested operational checks, not a record of workplace procedures.
- [`compose.yaml`](compose.yaml) — a **separate, illustrative local-only example** running Gitea and Stirling PDF. It uses Compose directly, not Dockge, and does not reproduce the workplace deployment. No validation results are provided; it is not presented as production-ready.
