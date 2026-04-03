Create a pytest conftest.py for a FastAPI application with PostgreSQL.

Include:
- Fixtures: async test client, test database session, authenticated user, admin user
- Factory functions: create_user, create_project, create_task (with realistic defaults)
- Test helpers: assert_response_ok, assert_validation_error, random_email, random_string
