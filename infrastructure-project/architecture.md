# Architecture and boundaries

## Workplace environment

This capability map summarizes the workplace environment; it is not an exact topology or a configuration export.

- **Host and management:** Ubuntu Server, with Docker Compose used to start Dockge. The other services were managed through Dockge.
- **Applications:** TAK server for ATAK and WinTAK clients, Gitea, Pi-hole, Stirling PDF, and Homarr dashboards.
- **Security tools:** Trivy, CrowdSec, Wazuh, and Nessus.
- **Connectivity and storage:** Starlink, a Cisco router, firewall services, and network-attached storage (NAS). Tailscale and MagicDNS supported named access to resources, including from outside the network.

The map does not specify routing, firewall rules, placement of individual components, or detailed data flows. MagicDNS provides names; it does not itself grant access. CrowdSec can detect suspicious activity and block IPs when an appropriate enforcement component is configured; its presence alone does not establish that enforcement is active. No original server certificates, addresses, rules, data, or private configuration are included here.

## Separate local Compose example

```text
Browser on Docker host
  ├─ 127.0.0.1:3000 → Gitea → named data volume
  └─ 127.0.0.1:8080 → Stirling PDF → config and storage volumes
```

The example uses Compose directly and contains only these two independent services. It does not set up Dockge, TAK, Tailscale, Pi-hole, the security tools, NAS, or network routing. Image versions must be selected and staged separately; no validation results are provided.

Ports bind to host loopback, not the LAN or tailnet. Loopback does not protect the applications from other users or processes on the same host. Shared access requires a separately designed access path, authorization, and appropriate transport security. See [Operations](operations.md) for setup and limitations.
