# Operations

The instructions below concern the separate local Compose example. The later checklist suggests practices for an authorized deployment; it is not a record of the original workplace procedures.

## Run the illustrative example

The sample starts Gitea and Stirling PDF directly with Compose, rather than reproducing the workplace Dockge workflow. It is not presented as validated or production-ready. Use a disposable host or isolated demo environment and demo-only credentials and data.

Prerequisites: a compatible Linux host (such as Ubuntu Server), Docker Engine, Docker Compose v2, internet access for the explicit image pull, and a browser on the Docker host. Image and application behavior can vary by version; consult the [Gitea Docker instructions](https://docs.gitea.com/installation/install-with-docker/) and [Stirling PDF Docker instructions](https://docs.stirlingpdf.com/Server/Install/Docker/).

1. Copy `.env.example` to `.env`. Set `GITEA_IMAGE` to an exact version or digest of the **rootful** `docker.gitea.com/gitea` image and `STIRLING_PDF_IMAGE` to an exact version or digest of `docker.stirlingpdf.com/stirlingtools/stirling-pdf`. Choose releases compatible with the host architecture, and review their licenses and release notes. Avoid floating `latest` tags. `.env` is ignored by Git.
2. From this folder, validate the configuration and explicitly stage the selected images:

   ```sh
   docker compose config -q
   docker compose pull
   docker compose up -d
   docker compose ps
   ```

   Compose is configured not to pull automatically when starting. If the host cannot access a registry, stage the same image references by another approved method instead.
3. On the host, open `http://127.0.0.1:3000/` and `http://127.0.0.1:8080/`. Complete the applications' initial setup with demo-only data. The example configures Gitea to use SQLite; create its administrator account during setup. Check that both interfaces respond. If they do not, inspect `docker compose logs --tail=100`; startup and configuration options depend on the selected versions.
4. Restart and revisit the interfaces to check persistence:

   ```sh
   docker compose restart
   docker compose ps
   ```

`docker compose down` stops the example and retains its named volumes. `docker compose down -v` deletes the demo data and should be used only when that is intended.

The loopback bindings do not protect the applications from other users or processes on the same host. The example has no remote-access policy, TLS proxy, backup automation, or monitoring. Before sharing services, plan authentication, authorization, transport security, updates, and recovery. Docker and Dockge access should be restricted to trusted administrators: control of the Docker daemon is highly privileged.

## Suggested operational checks

### Deploy and verify

- Record host and container versions, image digests, owners, access paths, and storage locations. Use a maintenance window and a tested rollback plan for changes.
- Check `docker compose ps` and `docker compose logs --tail=100` for startup errors. HTTP responses alone do not establish authentication, data protection, or application health.
- On a shared installation, test access with both authorized and unauthorized identities and devices. Check VPN policy and host firewall rules separately; DNS resolution is not authorization.
- For TAK, verify the approved server configuration and certificate lifecycle with its administrator; test representative ATAK/WinTAK clients. The example does not deploy or configure TAK.
- Scan authorized targets only. Review findings, remediate, and verify; the presence of Trivy, Wazuh, Nessus, or CrowdSec alone does not guarantee security. CrowdSec needs a correctly configured enforcement component to block traffic.

### Backups and recovery

- Inventory application data and configuration, including Gitea's repositories, database, and settings, Stirling PDF's `/configs` and `/storage`, and any other configured storage. Secrets and certificates require protected handling.
- Use each application's version-specific backup procedure, including a consistent database backup or a clean shutdown where appropriate. Encrypt and restrict backup access; keep a separate copy outside the host.
- Test restoration on an isolated host, verify sample data and access controls, and record the results. A NAS alone is not proof of a recoverable backup.
- Before upgrades, review release notes and migrations, back up, stage the new image, and validate the upgrade. A previous image may not be compatible with an upgraded database; restore a matching backup if rollback requires it.
