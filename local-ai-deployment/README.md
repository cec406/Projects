# Local AI deployment for low-bandwidth sites

**Portable local inference, task-specific agents, and an explicit cloud boundary.** This project shows how an AI workspace can be staged for sites where reliable broadband cannot be assumed.

## Experience and scope

I built and ran GPU-accelerated local LLMs and job-specific agents in an Arch Linux WSL environment. The agents could work from locally staged instructions, manuals, and reference material without relying on online search or a hosted model. I bundled Ollama, model files, and custom tools with the distribution so it could be transferred to another compatible Windows device rather than rebuilt or downloaded at each site. I selected models for available GPU VRAM and worked with models up to 24B parameters across the Qwen, DeepSeek, Mistral, Dolphin, and Gemma families. I also worked with containerized inference services and OpenCode configured for local models or OpenRouter.

**This repository is a synthetic reference implementation, not the original WSL distribution or private tools.** The [WSL runbook](wsl-portability.md) describes a clean reproduction of the portability workflow; the container lab below illustrates local inference and agent configuration. The files demonstrate the design, not a measured performance result or proof of a particular hardware deployment.

## Explore the evidence

| Area | What to review |
| --- | --- |
| Portable workspace | [WSL portability runbook](wsl-portability.md): staging, export/import, and offline acceptance checks. |
| Local inference | [Compose service](compose.yaml) binds Ollama to loopback and uses a persistent model volume; [`smoke.py`](smoke.py) checks the local catalog and requests a response. |
| Task-specific agents | [Local profile](config/local.json) defines a synthetic shift-handoff agent and a manual-answering agent with tool permissions denied; [the manual](config/manual-guide.md) is included as prompt context. |
| Cloud opt-in | [Connected profile](config/connected.json) selects an OpenRouter model in a separate workspace. It is not an automatic fallback. |

The example manual is loaded from disk into the agent's prompt; it does not use a vector database or retrieval service. Cloud requests may send prompts and context off-site, so use approved data only. The local profile restricts provider use at project scope, but an offline guarantee requires WAN isolation outside OpenCode.

## Deployment paths

```text
Local:   OpenCode → local Ollama API → GPU-backed inference (WSL or container host)
Remote:  Authorized user → Tailscale → on-site agents and GPU-backed inference
Cloud:   OpenCode → OpenRouter (separate workspace, explicitly selected)
```

For the portable Windows workflow, start with the [WSL runbook](wsl-portability.md). For the container reference, follow the steps below. The remote-access section describes the Tailscale pattern; the Compose sample does not configure it.

## Container lab: stage once, run without broadband

1. **Prepare the runtime.** On bare metal, verify the GPU with `nvidia-smi`. In a Proxmox lab, enable IOMMU and assign the GPU to a Linux guest through PCI passthrough; verify it with `nvidia-smi` inside the guest first. The sample assumes an NVIDIA GPU, working guest driver, NVIDIA Container Toolkit, and Docker Compose 2.30+ (`gpus: all`). Passthrough is a hypervisor setup step, not a Compose feature.
2. **Stage artifacts while connected.** Set `OLLAMA_IMAGE` to an exact, locally available Ollama tag or digest. Prepare OpenCode and any provider runtime dependencies on the actual target or an equivalent staging machine. From this directory on a connected target, start Ollama and download the model:

   ```sh
   export OLLAMA_IMAGE='ollama/ollama:<staged-tag>' # replace with your local tag or digest
   docker compose up -d
   docker compose exec ollama ollama pull qwen3:4b
   ```

   Keep `OLLAMA_IMAGE` set for subsequent Compose commands.

   For a target that never connects, transfer the container image (`docker save` / `docker load`) and a backup of the populated Ollama volume, including manifests and blobs. Restore the volume before starting Compose. Record image and artifact checksums, model license and platform architecture in the handoff. Docker is configured not to pull an absent image.
3. **Validate with WAN access blocked.** Run `docker compose up -d`, then `python smoke.py` using Python 3 on the container host. This checks that `qwen3:4b` is staged and returns text over the loopback API. After the request, run `docker compose exec ollama ollama ps` promptly and inspect `PROCESSOR` for GPU residency or CPU offload. The HTTP smoke test alone does not prove GPU acceleration.
4. **Run the agents.** Copy [`config/local.json`](config/local.json) to `opencode.json` in a clean demo workspace on the same host, and copy [`config/manual-guide.md`](config/manual-guide.md) next to it. Open OpenCode V2 from that workspace and give the `handoff` agent synthetic notes such as: “Bay 2 inspection complete. Replacement filter pending. ETA unknown.” Verify it preserves the facts and reports unknowns instead of guessing. Select `manual-guide` and ask: “What should I do if the Bay 2 replacement filter is out of stock?” Expect `Waiting for parts`, no ETA until purchasing confirms it, and a citation to `M-01`. Ask for a procedure not in the manual to check that the agent reports the gap instead of inventing instructions. Recheck after a container restart and with WAN access still blocked.

## Remote access to on-site AI over Tailscale

I used Tailscale to give remote users access to agents and local models running on a GPU-equipped host. The remote device did not need its own GPU or model files. Inference still ran on-site; this path requires a working network connection and is distinct from both the standalone WSL install and OpenRouter cloud inference.

The Compose sample stays bound to loopback and does not configure VPN access. For a shared deployment, keep the model API private, expose only the intended agent interface through an authenticated access path, and scope tailnet access to approved users and devices. Check access from an approved device and confirm an unapproved device cannot reach the service. No private addresses, account details, or access policies are included here.

## Optional connected mode

In a separate workspace, copy [`config/connected.json`](config/connected.json) to `opencode.json`. Set `PORTFOLIO_OPENROUTER_MODEL` to `openrouter/<vendor>/<model>` using a model available to your account, and provide `OPENROUTER_API_KEY` to the OpenCode service via its environment or use OpenCode's account connection. Do not commit credentials. OpenRouter requires internet and is not used by the local smoke test.

## What this demonstrates

A deployable inference service, an explicit offline/cloud boundary, and a task-specific agent with no shell or write access. Everything in the example is synthetic; no customer configuration, GPU inventory, model weights, keys, or private endpoints are included. This is a portfolio lab, not a hardened multi-user inference platform. No performance figures or hardware validation results are claimed.
