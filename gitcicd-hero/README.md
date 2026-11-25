# GitCI/CD Hero | Offline deployment training

A browser-based workshop for onboarding developers and operators to Git and CI/CD. Learners can make mistakes, inspect what happened, and retry without touching a live repository, workflow runner, or customer credentials.

**[Try GitCI/CD Hero live](https://grizzlyse.com/gitcicd/)** — no setup required.

The course has 8 tracks and 46 chapters, including simulated Git missions, CI missions, and quizzes. The browser engines let learners practice commands and workflow concepts in a controlled environment rather than using a real Git executable or CI runner.

## Try it locally

Open `index.html` from this folder in a browser. Start with a Git mission, then run a sample pipeline and inspect its job logs. No account or installation is required for the app. Git commands and pipeline steps run in a simulation, not on the host.

## Review the implementation

- [`js/git.js`](js/git.js): simulated working tree, staging area, commits and branches.
- [`js/ci.js`](js/ci.js): simulated workflow execution and results.
- [`tools/selftest.js`](tools/selftest.js): engine and lesson checks; run `node tools/selftest.js` with Node.js.

This is a training tool, not a replacement for Git or a production GitHub Actions runner.
