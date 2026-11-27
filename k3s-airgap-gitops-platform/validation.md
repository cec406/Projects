# Disconnected K3s workload: validation notes

I previously deployed this sample workload successfully in a disconnected K3s lab. I don’t have terminal output from that run attached here. The checks below document how to reproduce and capture the result; the expected results are not a transcript.

**Scope:** The `airgap-web` Zarf package only. This does not validate the separate Flux platform or its offline mirrors.

For a machine-readable staging and local HTTP report, see the [Edge Deployment Readiness Kit](../edge-readiness/). It complements the checks below; it doesn’t verify WAN isolation or the registry used by the pod.

## Capture a repeat run

1. Record the date, Git commit (`git rev-parse --short HEAD`), node architecture, K3s and Zarf versions, and the checksum of the package you transferred. Use a fresh lab node or verify the demo workload and image aren’t already present.
2. Stage the package and matching Zarf init package while connected. Before deploying, disable WAN access on the target while keeping local console access. Record how you isolated the node and capture a failed connection to the public registry (for example, `curl -I --max-time 5 https://registry-1.docker.io/v2/` **from the node**). Any HTTP response, including `401`, means the registry was reachable.
3. Follow the [offline workload walkthrough](README.md#run-the-offline-workload-demo) and save the deployment output. Then capture the following checks while the target is still isolated:

   ```sh
   kubectl -n zarf-demo rollout status deployment/airgap-web --timeout=120s
   kubectl -n zarf-demo get pods -l app=airgap-web \
     -o jsonpath='{range .items[*]}{.spec.containers[0].image}{"\n"}{end}'
   ```

   Expected: the rollout completes and the pod references the local Zarf registry, not Docker Hub.

4. In one terminal, run `kubectl -n zarf-demo port-forward deployment/airgap-web 8080:80`. In another, run `curl -i http://127.0.0.1:8080/`. Expected: HTTP 200 and the sample nginx page. The manifest defines a Deployment but no Service, so port-forwarding lets you verify the app without changing the manifests.
5. Save a short, dated transcript alongside this page, with private hostnames, addresses, and credentials removed. Include any failed checks or steps you had to change. A screen recording is optional.
