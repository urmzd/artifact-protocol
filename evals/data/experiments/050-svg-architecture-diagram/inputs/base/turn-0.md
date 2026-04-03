Create an SVG architecture diagram for a microservices application.

Include:
- Frontend tier: React app, CDN, load balancer (boxes with labels)
- Backend tier: API Gateway, Auth Service, User Service, Order Service, Notification Service
- Data layer: PostgreSQL, Redis, RabbitMQ, S3
- Connection arrows between components with labels (HTTP, gRPC, AMQP)
- Color coding by tier (blue frontend, green backend, orange data)
- Title and legend

Use section IDs: frontend, backend, data-layer, connections

Use AAP section markers to delineate each major block.
Wrap each logical section with `<aap:section id="ID">` and `</aap:section>`.


Output raw code only. No markdown fences, no explanation.