# Versioned container delivery

A commercial reference sample of the release pattern I used for containerized tooling: build an identifiable artifact, scan it, and verify it starts before promoting it to a customer host.

## Try it locally

From this directory, with Docker running:

```sh
docker build -t portfolio-release:demo .
docker run --rm -p 127.0.0.1:8080:8080 portfolio-release:demo
```

In a second terminal, run `curl http://127.0.0.1:8080/` and look for `release-ok`. The tiny HTTP response is just a smoke-test fixture, not a portfolio website.

## Review the pipeline

`release.yml` is a template, not an enabled workflow. To try it on GitHub, copy it to `.github/workflows/release.yml` at the repository root and trigger it manually. It tags the image with the commit SHA, gates on Trivy's high/critical findings, and checks the HTTP response. It does not push images or update hosts; a production rollout would promote the verified image by digest and retain the previous digest for rollback.
