Create an Ansible playbook for deploying a Python web application to Ubuntu servers.

Include:
- Variables: app name, version, deploy path, service user, Python version, Nginx config
- Pre-tasks: update apt, install system packages, create deploy user
- Server setup: install Python, create virtualenv, configure systemd service
- App deployment: clone repo, install dependencies, run migrations, collect static files
- Post-tasks: configure Nginx reverse proxy, enable SSL with certbot, restart services
- Handlers for service restarts

Use section IDs: vars, pre-tasks, roles-setup, app-deploy, post-tasks

Use AAP section markers to delineate each major block.
Wrap each logical section with `<aap:section id="ID">` and `</aap:section>`.


Output raw code only. No markdown fences, no explanation.