# Caleb E. Clark | Forward-deployed engineering

I build software around how operators work and deploy it on the infrastructure they have. My work spans shop operations software, workplace systems integration, disconnected deployment, and training that helps operators use what I build.

**[Live engineering portfolio](https://grizzlyse.com/portfolio/) · [Project catalog](https://grizzlyse.com/projects/) · [Engineering Lab](https://grizzlyse.com/lab.html) · [LinkedIn](https://www.linkedin.com/in/caleb-clark-4a638b28b/)**

## Start here

**Reviewing for a forward-deployed role?** Move a sample work order in GrizzWorks. Then read the workplace capability map to see how I integrated services within an existing network, or open the K3s validation notes if your team ships to disconnected sites.

| What to evaluate | Work sample | What to inspect |
| --- | --- | --- |
| Operator-facing software | **GrizzWorks** · Browser demo + self-hosted app. A work order flows through jobs, stock, quotes, and invoicing. The shared JavaScript engine posts balanced entries and corrects posted invoices with reversals. | [Try the seeded work-order board](https://grizzlyse.com/dashboard/?demo=1#/workorders) · [Wall display](https://grizzlyse.com/dashboard/display.html) · [Engine](grizzworks-engine/shared/erp.js) · [Tests](grizzworks-engine/tests/erp.test.js) · [Full Node app](https://github.com/cec406/applications/tree/main/dashboard) |
| Workplace integration and VPN | **Private field services** · Built an Ubuntu Server environment for TAK (ATAK/WinTAK) and self-hosted tools. Docker Compose bootstrapped Dockge; the site used Starlink, a Cisco router, firewall services, NAS, and Tailscale with MagicDNS. Security tooling included Trivy, CrowdSec, Wazuh, and Nessus. | [Capability map](infrastructure-project/architecture.md) · [Sample operations checks](infrastructure-project/operations.md) · [Independent VPN field notes](https://grizzlyse.com/lab.html#vpn) |
| Kubernetes under connectivity constraints | **Disconnected K3s delivery** · I deployed the sample web workload in a disconnected lab. Its Zarf package bundles the image and manifests. The separate Flux/Kustomize example shows persistent services and network policy; it still needs mirrors to run fully offline. | [Validation notes](k3s-airgap-gitops-platform/validation.md) · [Runbook](k3s-airgap-gitops-platform/) · [Zarf package](k3s-airgap-gitops-platform/zarf-packages/airgap-web/zarf.yaml) · [Flux manifests](k3s-airgap-gitops-platform/clusters/edge-node/) |
| Local AI and handoff | **Portable GPU inference** · Built an Arch WSL environment with Ollama, local models up to 24B parameters, and task-specific agents. Also used Tailscale to reach on-site inference. Public artifacts are synthetic examples, not the original distribution. | [WSL portability runbook](local-ai-deployment/wsl-portability.md) · [Container reference and offline checks](local-ai-deployment/) |
| Operator and developer enablement | **Grizzly Range and GitCI/CD Hero** · Five independent browser training apps, a shared progress view, and 12 graded work orders. GitCI/CD Hero includes 8 tracks and 46 chapters using simulated Git and CI engines. | [Range desktop](https://grizzlyse.com/range/) · [Range design notes](https://grizzlyse.com/portfolio/#range) · [Git engine](gitcicd-hero/js/git.js) · [CI engine](gitcicd-hero/js/ci.js) · [Self-test](gitcicd-hero/tools/selftest.js) |

The workplace documentation leaves out private configurations, credentials, and data. The [illustrative Compose file](infrastructure-project/compose.yaml) is a separate local example, not a workplace export. The GrizzWorks extract in this repository contains the shared engine, not the full application. Use sample data in public demos.

## Implementation and release handoff

**[GrizzWorks migration rehearsal](grizzworks-migration/)** — Review a messy CSV before writing a candidate backup, then verify the restore against a disposable GrizzWorks Node server. The recorded fixture run imported four work orders totaling 7.50 estimated hours, preserved the original row, and proposed zero new records on replay. See the [blocked preview](grizzworks-migration/reports/blocked.json) and [lab result](grizzworks-migration/reports/lab-result.json).

**[Edge Deployment Readiness Kit](edge-readiness/)** — A runnable Python CLI checks target architecture and package checksums before an operator deploys. Compare the [wrong-revision block](edge-readiness/reports/blocked.json) with the [passing staging report](edge-readiness/reports/staged.json). Both reports use synthetic files; the [post-deploy HTTP test](edge-readiness/test_readiness.py) runs against a local test server, not K3s.

## Supporting work

- **[Versioned container delivery](container-delivery/)** — a reference [pipeline](container-delivery/release.yml) builds and tags an image, runs a Trivy scan, and checks the HTTP response. It is not an active deployment workflow.
- **[Python and SQLite shop reference](shop-operations/)** — balanced ledger entries and repeat-safe event processing. A separate Python example, not the GrizzWorks backend.
- **[AFT Forge](https://grizzlyse.com/aft-forge/)** — React/TypeScript fitness planner with local data, backup export, and a [Pages build and verification workflow](https://github.com/cec406/grizzlyse/blob/main/.github/workflows/deploy.yml).
- **[Deployment playbook](https://grizzlyse.com/solutions.html)** — operator discovery, go-live criteria, fallback, and handoff. The worked example is a rollout plan, not a client outcome.
- **[Python apps and games](https://grizzlyse.com/projects/#python)** — Tkinter and terminal utilities, Python/SQLite, and defensive security tools. See the [games section](https://grizzlyse.com/projects/#games) for Pygame and text adventures.
- **[Learning apps and simulations](https://grizzlyse.com/projects/#education)** — math, computing and security awareness. The catalog also covers [language practice](https://grizzlyse.com/projects/#languages) and live browser games.

## Repository map

| Repository | Start here |
| --- | --- |
| **Projects** (this repo) | Evidence index: project READMEs, reference manifests, runbooks, and focused source samples. |
| **[grizzlyse](https://github.com/cec406/grizzlyse)** | Source for the public site, portfolio, Pages workflow, and browser apps. |
| **[applications](https://github.com/cec406/applications)** | Deployable GrizzWorks and Shop Ops source, tests, and packaging. |
| **[Python-applications](https://github.com/cec406/Python-applications)** | Tkinter utilities, Pygame, and console projects. |

For the account landing page, use the canonical [GitHub profile README draft](GITHUB-PROFILE.md). It only becomes the profile README after it is copied to the root of `cec406/cec406`; editing this repository does not change the account profile.

**Recruiting:** [Email Caleb](mailto:info@grizzlyse.com?subject=Recruiting%20inquiry%20for%20Caleb%20Clark) · [LinkedIn](https://www.linkedin.com/in/caleb-clark-4a638b28b/) · [GitHub profile](https://github.com/cec406)
