Create a docker-compose.yaml for a microservices application with:

- API gateway (nginx) on port 80
- Auth service (Node.js) with JWT config
- User service (Python/FastAPI) with PostgreSQL
- Order service (Go) with Redis cache
- Notification service (Python) with RabbitMQ
- PostgreSQL database with initialization
- Redis cache
- RabbitMQ message broker
- Shared network and named volumes
- Health checks for each service
- Environment variables and .env file references

Use section IDs: services, networks, volumes

Use AAP section markers to delineate each major block.
Wrap each logical section with `<aap:section id="ID">` and `</aap:section>`.


Output raw code only. No markdown fences, no explanation.