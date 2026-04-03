Create a bash deployment script for a Node.js application to a remote server.

Include:
- Configuration: server host, deploy path, app name, Node version, env vars
- Pre-deploy checks: git status clean, tests pass, correct branch, SSH connectivity
- Build: install dependencies, run build, create tarball
- Deploy: upload to server, extract, install production deps, run migrations, swap symlink, restart PM2
- Post-deploy verification: health check endpoint, log tail, rollback on failure
- Colored output, error handling with set -euo pipefail

Use section IDs: config, checks, build, deploy, verify

Use AAP section markers to delineate each major code block.
Wrap each logical section with `<aap:section id="ID">` and `</aap:section>`.


Output raw code only. No markdown fences, no explanation.