Create a GitHub Actions CI/CD workflow for a TypeScript monorepo.

Include:
- Triggers: push to main, pull_request, manual dispatch
- Lint job: checkout, setup Node, install deps, run eslint and prettier check
- Test job: matrix (Node 18, 20), run vitest with coverage, upload coverage artifact
- Build job: depends on lint+test, build Next.js app, upload build artifact
- Deploy job: depends on build, deploy to Vercel (staging on PR, production on main push)
- Concurrency control, caching for node_modules

Use section IDs: triggers, lint-job, test-job, build-job, deploy-job

Use AAP section markers to delineate each major block.
Wrap each logical section with `<aap:section id="ID">` and `</aap:section>`.


Output raw code only. No markdown fences, no explanation.