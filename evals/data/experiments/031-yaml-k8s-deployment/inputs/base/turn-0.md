Create Kubernetes manifests for deploying a web application.

Include:
- Deployment: 3 replicas, rolling update strategy, resource limits, liveness/readiness probes, env from configmap/secret
- Service: ClusterIP type, port 80 targeting 8080
- Ingress: with TLS, host-based routing, path prefixes
- HorizontalPodAutoscaler: min 2, max 10, CPU target 70%
- ConfigMap: application configuration (database URL, cache TTL, log level, feature flags)

Use section IDs: deployment, service, ingress, hpa, configmap

Use AAP section markers to delineate each major block.
Wrap each logical section with `<aap:section id="ID">` and `</aap:section>`.

Separate each manifest with `---`.

Output raw code only. No markdown fences, no explanation.