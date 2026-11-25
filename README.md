# Caleb E. Clark · Forward Deployed Engineering

I build and deploy software for teams that need it to work on existing hardware, with limited connectivity and a small crew to operate it.

[Connect on LinkedIn](https://www.linkedin.com/in/caleb-clark-4a638b28b/) · [GitHub profile](https://github.com/cec406)

## Featured work

| Project | Customer problem | Start here |
| --- | --- | --- |
| **[Local AI deployment](local-ai-deployment/)** | Keep task-specific assistants usable when the internet link drops. | [Portable Arch WSL runbook](local-ai-deployment/wsl-portability.md): GPU-backed Ollama, offline OpenCode agents with local manuals, and a separate Tailscale path for remote users. |
| **[GrizzWorks](grizzworks-engine/)** | Run shop billing and inventory on-site without depending on SaaS. | [Try the full demo](https://grizzlyse.com/dashboard/) or [review the engine tests](grizzworks-engine/tests/erp.test.js). The repo includes the shared business logic, not the full app. |
| **[Disconnected Kubernetes delivery](k3s-airgap-gitops-platform/)** | Deploy software where target systems cannot pull from public registries. | [Offline deployment walkthrough](k3s-airgap-gitops-platform/#run-the-offline-workload-demo) for a packaged K3s workload, plus a separate Flux GitOps example. |
| **[GitCI/CD Hero](gitcicd-hero/)** | Train operators without giving them access to production pipelines. | [Try the live simulator](https://grizzlyse.com/gitcicd/) or review the browser-based Git and CI engines. |

## Supporting samples

- [Versioned container delivery](container-delivery/) — build, scan, and smoke-test a commit-tagged image.
- [Local-first shop operations](shop-operations/) — a small Python/SQLite example of balanced ledger entries and safe replay.

The READMEs distinguish original project code from reference implementations. Examples use generic workloads and synthetic data, not customer deployments.
