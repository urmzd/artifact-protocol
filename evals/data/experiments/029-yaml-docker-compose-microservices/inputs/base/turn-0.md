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
