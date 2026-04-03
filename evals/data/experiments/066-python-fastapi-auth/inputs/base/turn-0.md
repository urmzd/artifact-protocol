Create a FastAPI authentication module with JWT tokens.

Include:
- Config: secret key, algorithm, token expiry settings
- JWT utilities: create_access_token, create_refresh_token, verify_token, decode_token
- Dependency functions: get_current_user, require_role, optional_auth
- Routes: POST /auth/register, POST /auth/login, POST /auth/refresh, POST /auth/logout, GET /auth/me
- Password hashing with bcrypt pattern
- Proper error responses for expired/invalid tokens
