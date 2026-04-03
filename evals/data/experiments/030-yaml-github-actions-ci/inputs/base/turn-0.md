Create a GitHub Actions CI/CD workflow for a TypeScript monorepo.

Include:
- Triggers: push to main, pull_request, manual dispatch
- Lint job: checkout, setup Node, install deps, run eslint and prettier check
- Test job: matrix (Node 18, 20), run vitest with coverage, upload coverage artifact
- Build job: depends on lint+test, build Next.js app, upload build artifact
- Deploy job: depends on build, deploy to Vercel (staging on PR, production on main push)
- Concurrency control, caching for node_modules
