Create a comprehensive pytest test suite for a user authentication system.

Include:
- Fixtures: test database, test client, sample users (admin, regular, inactive), auth headers
- Registration tests: valid signup, duplicate email, weak password, missing fields, email validation
- Login tests: valid login, wrong password, inactive user, rate limiting, token refresh
- Permission tests: admin-only endpoints, resource ownership, role escalation prevention
- Use parametrize for edge cases, proper assertions with descriptive messages
