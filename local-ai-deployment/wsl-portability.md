# Portable GPU-accelerated AI workspace on Arch WSL

The original workflow used an Arch Linux WSL environment with Ollama, local models, and custom agents and tools for specific jobs. The handoff was the working environment itself: package it once, transfer it, and import it on another compatible Windows device. This runbook describes a clean commercial reproduction using synthetic input, not a download of the original image.

## Build and stage a clean image

- Use a dedicated Arch WSL 2 distribution. Install the runtime and job tools in the Linux filesystem, not under `/mnt/c`, so they travel with the export. Stage the Ollama models under the account that runs Ollama (or a documented `OLLAMA_MODELS` directory). Record versions, model licenses, default user, and service startup steps.
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
2. Run `python smoke.py` from this project inside WSL, or use `--model` to select the staged model. Immediately run `ollama ps` and inspect `PROCESSOR` to confirm GPU use rather than just a successful CPU response.
3. Launch OpenCode inside WSL with the [local profile](config/local.json) in a clean workspace. Run the synthetic shift-handoff task from the [project README](README.md). Verify the assistant uses the local endpoint and preserves the supplied facts.
4. Restart the imported distro and repeat the checks. Record what had to be configured on the Windows host versus what was restored from the bundle.

The portable WSL route does not require Docker. The separate container route is useful when the installation target already runs containerized services. Neither route needs OpenRouter for local inference.
