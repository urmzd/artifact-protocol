Create a Rust error handling module for a web application.

Include:
- AppError enum with variants: NotFound, Unauthorized, Forbidden, ValidationError, DatabaseError, ExternalServiceError, RateLimited, InternalError
- Display and Error trait implementations
- From implementations for common error types (sqlx::Error, reqwest::Error, serde_json::Error, std::io::Error)
- Into HTTP response conversion (status code + JSON error body)
- Helper constructors and Result type alias
