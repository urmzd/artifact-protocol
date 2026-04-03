Create a TypeScript API client class for a project management API.

Include:
- Types: Project, Task, User, Comment, ApiResponse<T>, PaginatedResponse<T>, ApiError
- ApiClient class: constructor with baseURL and auth token, generic request method
- Endpoint methods: projects CRUD, tasks CRUD, assign task, add comment, upload attachment
- Request/response interceptors: auth header injection, error transformation, retry logic, request logging
- Proper TypeScript generics throughout
