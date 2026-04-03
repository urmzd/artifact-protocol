Create ASGI middleware classes for a Python web application.

Include:
- Base middleware class with __init__ and __call__ pattern
- AuthMiddleware: verify JWT, attach user to request, skip public paths
- LoggingMiddleware: request/response logging with timing, request ID generation, structured JSON output
- RateLimiter: sliding window per IP, configurable limits, Redis-backed counter, 429 responses
- CORSMiddleware: configurable origins, methods, headers, credentials, preflight caching
