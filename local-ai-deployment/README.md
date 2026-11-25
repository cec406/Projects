# Local AI deployment for low-bandwidth sites

I built and ran GPU-accelerated local LLMs and job-specific agents inside an Arch Linux WSL environment. I bundled the distribution with Ollama, model files, and custom tools so I could transfer the environment to another Windows device instead of rebuilding it or downloading models at each site. I used different models based on available GPU VRAM, working with models up to 24B parameters across Qwen, DeepSeek, Mistral, Dolphin, and Gemma families. I also worked with containerized inference services and OpenCode configured for either local models or OpenRouter.

This folder is a commercial reference implementation, not the original distribution or a copy of private tools. It documents two deployment paths: [the portable Arch WSL bundle](wsl-portability.md) and the container lab below. The goal is the same for both: a technician can use an assistant after the WAN link drops, and the operator decides when cloud inference is allowed.

```text
Offline:    OpenCode → local model API → Ollama container → GPU in Linux guest
Remote:     Authorized user → Tailscale → on-site agents and GPU-backed inference
Cloud:      OpenCode → OpenRouter (separate workspace, explicitly selected)
```

I used OpenCode with local LLMs and built separate agents for different jobs. Each could work from the instructions, manuals, and reference material staged with its environment, rather than depending on an online search or hosted model.

This repo illustrates that pattern with two agents: `handoff` turns synthetic notes into a shift summary, and `manual-guide` answers questions from a bundled local manual. The offline profile selects the local model, allows only the local provider at project scope, and denies agent tool use. The manual is loaded into the second agent's prompt from disk; this small example does not need a vector database or retrieval service. The connected profile is opt-in, not an automatic fallback. Cloud requests may send the prompt and context off-site. Use approved data only; for an offline guarantee, enforce WAN isolation outside OpenCode rather than relying on project settings.

## Stage once, run without broadband

1. **Prepare the runtime.** On bare metal, verify the GPU with `nvidia-smi`. In a Proxmox lab, enable IOMMU and assign the GPU to a Linux guest through PCI passthrough; verify it with `nvidia-smi` inside the guest first. The sample assumes an NVIDIA GPU, working guest driver, NVIDIA Container Toolkit, and Docker Compose 2.30+ (`gpus: all`). Passthrough is a hypervisor setup step, not a Compose feature.
2. **Stage artifacts while connected.** Set `OLLAMA_IMAGE` to an exact, locally available Ollama tag or digest. Prepare OpenCode and any provider runtime dependencies on the actual target or an equivalent staging machine. On a connected target, start Ollama and download the model:

   ```sh
   docker compose up -d
   docker compose exec ollama ollama pull qwen3:4b
   ```

   For a target that never connects, transfer the container image (`docker save` / `docker load`) and a backup of the populated Ollama volume, including manifests and blobs. Restore the volume before starting Compose. Record image and artifact checksums, model license and platform architecture in the handoff. Docker is configured not to pull an absent image.
3. **Validate with WAN access blocked.** Run `docker compose up -d`, then `python smoke.py` using Python 3 on the container host. This checks that `qwen3:4b` is staged and returns text over the loopback API. After the request, run `docker compose exec ollama ollama ps` promptly and inspect `PROCESSOR` for GPU residency or CPU offload. The HTTP smoke test alone does not prove GPU acceleration.
4. **Run the agent.** Copy [`config/local.json`](config/local.json) to `opencode.json` in a clean demo workspace on the same host. Open OpenCode V2 from it and give the `handoff` agent synthetic notes such as: “Bay 2 inspection complete. Replacement filter pending. ETA unknown.” Verify it preserves the facts and reports unknowns instead of guessing. For the second agent, copy [`config/manual-guide.md`](config/manual-guide.md) next to the workspace's `opencode.json`, select `manual-guide`, and ask: “What should I do if the Bay 2 replacement filter is out of stock?” Expect `Waiting for parts`, no ETA until purchasing confirms it, and a citation to `M-01`. Ask for a procedure not in the manual to check that the agent reports the gap instead of inventing instructions. Recheck after a container restart and with WAN access still blocked.

## Remote access to on-site AI over Tailscale

I used Tailscale to give remote users access to agents and local models running on a GPU-equipped host. The remote device did not need its own GPU or model files. Inference still ran on-site; this path requires a working network connection and is distinct from both the standalone WSL install and OpenRouter cloud inference.

The Compose sample stays bound to loopback and does not configure VPN access. For a shared deployment, keep the model API private, expose only the intended agent interface through an authenticated access path, and scope tailnet access to approved users and devices. Check access from an approved device and confirm an unapproved device cannot reach the service. No private addresses, account details, or access policies are included here.

## Optional connected mode

In a separate workspace, copy [`config/connected.json`](config/connected.json) to `opencode.json`. Set `PORTFOLIO_OPENROUTER_MODEL` to `openrouter/<vendor>/<model>` using a model available to your account, and provide `OPENROUTER_API_KEY` to the OpenCode service via its environment or use OpenCode's account connection. Do not commit credentials. OpenRouter requires internet and is not used by the local smoke test.

## What this demonstrates

A deployable inference service, an explicit offline/cloud boundary, and a task-specific agent with no shell or write access. Everything in the example is synthetic; no customer configuration, GPU inventory, model weights, keys, or private endpoints are included. This is a portfolio lab, not a hardened multi-user inference platform. No performance figures or hardware validation results are claimed.
