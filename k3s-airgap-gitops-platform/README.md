# Air-Gapped & Tactical-Edge Kubernetes GitOps Platform (K3s + Zarf + Flux CD)

A declarative, security-hardened Kubernetes platform engineered to model **Disconnected, Intermittent, and Limited-Bandwidth (DDIL)** tactical-edge operations. Built on **K3s**, packaged for air-gapped delivery with **Zarf**, reconciled declaratively via **Flux CD** against a self-hosted **Gitea** instance, and hardened with zero-trust **NetworkPolicies**, continuous **Trivy** vulnerability scanning, and automated **Kured** node lifecycle management.

## Architecture Overview

```text
+-----------------------------------------------------------------------------------+
|                        Disconnected / Tactical-Edge Node (K3s)                    |
|                                                                                   |
|  [ Zarf Air-Gap Bundle (.tar.zst + SBOM) ]                                        |
|          |                                                                        |
|          v                                                                        |
|  +---------------------------+      Mutating Webhook      +--------------------+  |
|  |   Zarf Local OCI Registry | <------------------------> |     Zarf Agent     |  |
|  +---------------------------+      Rewrites Image URLs   +--------------------+  |
|                                                                                   |
|  +---------------------------+      GitOps Reconcile      +--------------------+  |
|  |   Self-Hosted Gitea       | <------------------------> |   Flux CD Engine   |  |
|  |  (Isolated PostgreSQL DB) |                            +--------------------+  |
|  +---------------------------+                                      |             |
|          ^                                                          v             |
|          | NetworkPolicy (TCP/5432)            +-------------------------------+  |
|  +---------------------------+                 |   Hardened Edge Workloads     |  |
|  |  Aqua Trivy Operator      |                 | - Traefik Ingress             |  |
|  |  (Continuous CVE / SBOM)  |                 | - Prometheus & Grafana        |  |
|  +---------------------------+                 | - Uptime Kuma                 |  |
|                                                | - Kured (OS Reboot Lifecycle) |  |
|                                                +-------------------------------+  |
+-----------------------------------------------------------------------------------+
```

## Key Capabilities & Stack

- **Air-Gap Application Delivery (Zarf):** Bundles Kubernetes manifests, container images, and Software Bills of Materials (SBOMs) into portable `.tar.zst` archives (`zarf-packages/airgap-web/zarf.yaml`). Uses Zarf's mutating admission webhook (`zarf-agent`) to dynamically rewrite external registry references to an in-cluster OCI registry.
- **Declarative GitOps (Flux CD + Self-Hosted Gitea):** Eliminates external SaaS dependencies by hosting Git repositories locally in Gitea backed by persistent PostgreSQL storage, with Flux CD continuously reconciling cluster state (`Kustomization` and `HelmRelease` CRDs).
- **Zero-Trust Micro-Segmentation (`NetworkPolicy`):** Enforces namespace-level ingress isolation (`allow-gitea-only`) so stateful database workloads only accept traffic from authorized application namespaces.
- **Continuous Vulnerability & Compliance Telemetry (Aqua Trivy Operator):** Continuously scans running workloads for CVEs, exposed secrets, and misconfigurations to support Continuous ATO (cATO) workflows.
- **Observability & Automated Node Lifecycle:** Full-stack metrics and alerting via `kube-prometheus-stack` (Prometheus, Grafana, Alertmanager), endpoint health checks via Uptime Kuma, and automated maintenance-window OS patching reboots via **Kured**.

## Repository Structure

```text
├── clusters/edge-node/          # Flux CD Kustomizations and HelmReleases (Kured, Trivy, Monitoring)
├── zarf-packages/airgap-web/    # Zarf package definition (zarf.yaml) and air-gapped workload manifests
├── infrastructure/
│   ├── postgres/                # Stateful PostgreSQL deployment, PVC, and zero-trust NetworkPolicy
│   ├── gitea/                   # Self-hosted Gitea Git server and Traefik Ingress
│   ├── monitoring/              # kube-prometheus-stack HelmRelease and alert rules
│   └── uptime-kuma/             # Service availability and internal DNS health monitoring
└── README.md
```

## Quickstart: Air-Gap Packaging & Deployment

1. **Package the workload on a connected build host:**
   ```bash
   cd zarf-packages/airgap-web
   zarf package create --confirm
   ```
2. **Initialize Zarf and deploy on the disconnected cluster:**
   ```bash
   zarf init --confirm
   zarf package deploy zarf-package-edge-airgap-demo-amd64-0.1.0.tar.zst --confirm
   ```
3. **Verify mutating webhook image rewriting:**
   ```bash
   kubectl get pod -n zarf-demo -o jsonpath='{.items[0].spec.containers[0].image}{"
"}'
   ```
