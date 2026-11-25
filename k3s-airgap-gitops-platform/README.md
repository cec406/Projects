# Disconnected Kubernetes delivery | K3s, Zarf and Flux CD

This lab shows how to deliver an application to a remote commercial site that cannot pull from public registries. It separates the **offline workload demo** from the **GitOps platform example** so operators know which components still need mirrors.

## Run the offline workload demo

Use a disposable amd64 K3s cluster and a Zarf CLI and init package from the same release. Ensure the Kubernetes context points at the lab cluster before running the deployment commands.

1. On a connected build machine, from this project directory:

   ```sh
   cd zarf-packages/airgap-web
   zarf package create --confirm
   ```

2. Transfer the generated package and the matching amd64 Zarf init package to the offline operator machine through your approved transfer process. From the directory containing both archives:

   ```sh
   zarf init --confirm
   zarf package deploy ./zarf-package-edge-airgap-demo-amd64-0.1.0.tar.zst --confirm
   ```

3. Check that the pod is ready and inspect the running pod's image reference:

   ```sh
   kubectl -n zarf-demo rollout status deployment/airgap-web --timeout=120s
   kubectl -n zarf-demo get pods -l app=airgap-web -o jsonpath='{range .items[*]}{.spec.containers[0].image}{"\n"}{end}'
   ```

   The pod should use the Zarf registry rather than pulling the original image from Docker Hub.

## Review the GitOps platform

- [`clusters/edge-node/`](clusters/edge-node/) contains a Flux reconciliation example and optional Helm releases for monitoring, vulnerability scanning and reboot scheduling. Review Kured's maintenance window before enabling it.
- [`infrastructure/`](infrastructure/) contains Gitea, PostgreSQL, Uptime Kuma and an ingress policy that allows Gitea pods to reach PostgreSQL. Policy enforcement requires a compatible network plugin.
- [`zarf-packages/airgap-web/`](zarf-packages/airgap-web/) packages only the sample web workload, not the entire platform.

For the GitOps example, bootstrap Flux against a reachable Git repository first. The sample `edge-infrastructure` resource assumes the `flux-system` GitRepository points to the **parent portfolio repository**. If you publish this folder as a standalone repository, change `spec.path` to `./infrastructure` and update the bootstrap path accordingly. Do not point Flux at the example Gitea service until that service is available and has been seeded.

Before reconciling infrastructure, ensure the `postgres` and `gitea` namespaces exist and provision `postgres-credentials` in `postgres` and `gitea-db-secret` in `gitea`. Both need a `password` key containing the same value; provision it outside Git. PVCs require a default StorageClass or an explicitly configured one. The sample ingress names require matching local DNS and an ingress controller; configure TLS and access controls before exposing them beyond a lab.

The optional Helm releases reference public chart repositories. For a fully disconnected platform, mirror the charts, component images and Trivy vulnerability databases, then point configuration at the mirrors. This repository does not automate those steps. No ML workload is included.
