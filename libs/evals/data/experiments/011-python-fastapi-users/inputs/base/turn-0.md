Create a FastAPI user management module with full CRUD operations.

Include:
- SQLAlchemy models for User (id, email, name, hashed_password, role, is_active, created_at)
- Pydantic schemas for UserCreate, UserUpdate, UserResponse, UserList
- CRUD functions (create_user, get_user, list_users with pagination, update_user, delete_user)
- FastAPI router with endpoints: POST /users, GET /users, GET /users/{id}, PUT /users/{id}, DELETE /users/{id}
- Proper error handling with HTTPException
