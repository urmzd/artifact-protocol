Create an OpenAPI 3.0 specification in JSON for a bookstore API.

Include:
- Info with title "Bookstore API", version, description, contact
- Paths: /books (GET list, POST create), /books/{id} (GET, PUT, DELETE), /authors, /categories, /orders, /reviews
- Each endpoint with parameters, request body, responses (200, 400, 404, 500)
- Component schemas: Book, Author, Category, Order, Review, PaginatedResponse, ErrorResponse
- Security scheme: Bearer JWT
- At least 8 endpoints with full request/response schemas

