# Portable GPU-accelerated AI workspace on Arch WSL

The original workflow used an Arch Linux WSL environment with Ollama, local models, and custom agents and tools for specific jobs. The handoff was the working environment itself: package it once, transfer it, and import it on another compatible Windows device.

This is a runbook for a clean reference reproduction using synthetic input, **not the original image or private tools**. It describes what to stage and verify; this repository does not include a WSL distribution, model weights, or a recorded hardware validation. For the separate container lab and project overview, see the [README](README.md).

## Build and stage a clean image

- Use a dedicated Arch WSL 2 distribution. Install Ollama, OpenCode, required provider dependencies, and job tools in the Linux filesystem, not under `/mnt/c`, so they travel with the export. Include this project's smoke test and demo configuration if you plan to run the checks offline. Stage the Ollama models under the account that runs Ollama (or a documented `OLLAMA_MODELS` directory). Record versions, model licenses, default user, and service startup steps.
- WSL GPU acceleration uses the Windows host driver and WSL GPU support; it is distinct from assigning a PCI device directly to a Proxmox VM. Each destination needs compatible Windows, WSL 2, GPU hardware, and a supported host driver. The export does not carry those prerequisites.
- Build the shareable image from a clean distro rather than exporting a daily-use one. Exclude credentials, shell history, private repositories, chat logs, job data, and host-specific settings. Stage only models and tools you can redistribute. Do not commit the image or weights to Git.

## Transfer and import

Example PowerShell commands. Stop jobs before terminating the source distribution. Use a new name and an empty, dedicated destination directory on the receiving device.

```powershell
# Source: use the actual registered distro name from wsl --list --verbose
wsl --terminate Arch-AI
wsl --export Arch-AI .\arch-ai.tar
Get-FileHash .\arch-ai.tar -Algorithm SHA256

# Destination: compare the hash against the source before importing
Get-FileHash .\arch-ai.tar -Algorithm SHA256
wsl --import Arch-AI-Lab C:\WSL\Arch-AI-Lab .\arch-ai.tar --version 2
wsl -d Arch-AI-Lab -u YOUR_LINUX_USER
```

The WSL export is a tar archive; compress it separately for transfer if useful, then extract the tar before import. An imported distribution may default to root; use the intended Linux account and document default-user setup. Review `/etc/wsl.conf` on the staged image if service startup depends on systemd.

## Acceptance check on the receiving device

1. Block WAN access while retaining local loopback. Start Ollama from the imported distro with the same service user and model store that were staged. `ollama list` should show the model without a pull.
2. From this project directory inside WSL, run `python smoke.py`. It defaults to `qwen3:4b`; use `python smoke.py --model <staged-model>` for another model. Immediately run `ollama ps` and inspect `PROCESSOR` to confirm GPU use rather than just a successful CPU response.
3. In a clean workspace inside WSL, copy the [local profile](config/local.json) to `opencode.json` and place [the manual](config/manual-guide.md) beside it. If using a different model, update the profile's model selection and catalog entry to match. Launch OpenCode and run the synthetic shift-handoff task from the [project README](README.md). Verify the assistant uses the local endpoint and preserves the supplied facts.
4. Restart the imported distro and repeat the checks. Record what had to be configured on the Windows host versus what was restored from the bundle.

The portable WSL route does not require Docker. The separate container route is useful when the installation target already runs containerized services. Neither route needs OpenRouter for local inference.
