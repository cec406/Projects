# Caleb E. Clark

**Forward-deployed engineering · Infrastructure · Local AI · Software · Training**

I build and deploy software for teams working with existing hardware, limited connectivity, and a small crew to operate it.

[LinkedIn](https://www.linkedin.com/in/caleb-clark-4a638b28b/) · [GitHub](https://github.com/cec406) · [Explore the live lab](https://grizzlyse.com/lab) · [Browse all projects](https://grizzlyse.com/projects/)

## Selected work

### [Workplace infrastructure](infrastructure-project/) · Ubuntu Server, containers, networking

Built a workplace server running TAK for ATAK/WinTAK alongside self-hosted tools. Docker Compose started Dockge; other services were managed through Dockge. The environment included Starlink, a Cisco router, firewall services, NAS, and Tailscale VPN with MagicDNS for remote access.

Services included Gitea, Pi-hole, Stirling PDF, and Homarr; security tools included Trivy, CrowdSec, Wazuh, and Nessus. CrowdSec helped detect and block suspicious IP addresses.

[Capability map](infrastructure-project/architecture.md) · [Operations checklist](infrastructure-project/operations.md) · [Sanitized Compose example](infrastructure-project/compose.yaml) — a separate local example, not the workplace configuration.

### [Local AI deployment](local-ai-deployment/) · Ollama, WSL, GPU inference

Built a portable Arch WSL environment with local models and job-specific agents for low-bandwidth settings. Worked with Qwen, DeepSeek, Mistral, Dolphin, and Gemma models up to 24B parameters, selecting models based on available GPU VRAM. Also used Tailscale for remote access to on-site agents and inference.

[Portable WSL runbook](local-ai-deployment/wsl-portability.md) · [Container lab and offline checks](local-ai-deployment/) — reference implementations, not the original distribution or private tools.

### [GrizzWorks](grizzworks-engine/) · Local-first shop software

A shop operations app for jobs, invoices, inventory, and maintenance, with a locally hosted mode and browser demo. The shared engine applies business rules across both modes.

[Try the demo](https://grizzlyse.com/dashboard/) · [Read the engine](grizzworks-engine/shared/erp.js) · [Review the tests](grizzworks-engine/tests/erp.test.js) — this portfolio contains the shared engine, not the full app; use sample data in the public demo.

### [GitCI/CD Hero](gitcicd-hero/) · Browser-based technical training

Practice Git and CI/CD without touching a live repository or runner. The browser app simulates Git operations and pipeline execution across 8 tracks and 46 chapters, with 15 Git missions, 10 CI missions, and 21 quizzes.

[Try the live simulator](https://grizzlyse.com/gitcicd/) · [Git engine](gitcicd-hero/js/git.js) · [CI engine](gitcicd-hero/js/ci.js) · [Self-test](gitcicd-hero/tools/selftest.js)

### [Disconnected Kubernetes delivery](k3s-airgap-gitops-platform/) · K3s, Zarf, Flux

A lab for delivering a sample workload without pulling from a public registry at the target site. The offline workload and the GitOps platform are separate examples; a fully disconnected platform requires additional mirroring.

[Offline workload walkthrough](k3s-airgap-gitops-platform/#run-the-offline-workload-demo) · [Flux example](k3s-airgap-gitops-platform/clusters/edge-node/) · [Zarf package](k3s-airgap-gitops-platform/zarf-packages/airgap-web/)

## More to explore

**Delivery and application samples**

- [Versioned container delivery](container-delivery/) — reference build, Trivy scan, and smoke test; see the [pipeline template](container-delivery/release.yml).
- [Local-first shop operations](shop-operations/) — Python/SQLite reference for balanced ledger entries and repeatable imports.

**Live training and tools** · Built and hosted at [grizzlyse.com](https://grizzlyse.com). The [Range](https://grizzlyse.com/range/) brings five training machines together in a browser-based operator desktop.

- [Cyber Aware](https://grizzlyse.com/range/machine.html?m=csia) — employee cybersecurity course and assessment.
- [CSMath Hero](https://grizzlyse.com/csmath) — offline math practice from arithmetic through calculus, discrete math, linear algebra, probability, and algorithm analysis.
- [ZeroDay Academy](https://grizzlyse.com/range/machine.html?m=compsci) — simulated command lines, programming, networking, and authorized security practice.
- [GRIZZLY_SE Cyber Range](https://grizzlyse.com/range/machine.html?m=gsehack) — beginner security exercises in a game.
- [CODEWATCH](https://grizzlyse.com/range/machine.html?m=cybercrime) — cybercrime investigation and incident reporting simulation.
- [SpanishPod](https://grizzlyse.com/spanish) and [RussianPod](https://grizzlyse.com/russian) — language practice with graded lessons and games; SpanishPod uses Latin-American Spanish.
- [Station Demokratiya](https://grizzlyse.com/stationdemokratiya) — Russian and Spanish typing-defense game.
- [AFT Forge](https://grizzlyse.com/aft-forge/) — local-first fitness planning app built with React and TypeScript.

## Other repositories

- [Applications](https://github.com/cec406/applications) — shop operations and business applications.
- [grizzlyse](https://github.com/cec406/grizzlyse) — the live website, training apps, games, and language tools.
- [Cyber](https://github.com/cec406/Cyber) — security utilities and educational examples.
- [Python applications](https://github.com/cec406/Python-applications) — Python utilities and games.

Project READMEs distinguish original code and workplace experience from reference implementations and synthetic examples.
