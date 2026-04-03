Create API documentation in Markdown for a project management REST API.

Include:
- Authentication section: API key and OAuth2 flows, token refresh, example headers
- Users endpoints: list, get, create, update, delete — each with method, path, parameters, request body, response example, error cases
- Projects endpoints: CRUD plus members, tasks, milestones — same detail level
- Error codes reference table with code, message, description
- Rate limiting: limits, headers, retry-after behavior
- Use fenced code blocks for all examples (curl, JSON responses)

At least 12 fully documented endpoints.

Use section IDs: authentication, users-endpoints, projects-endpoints, errors, rate-limiting

Use AAP section markers to delineate each major content block.
Wrap each logical section with `<aap:section id="ID">` and `</aap:section>`.


Output raw code only. No markdown fences, no explanation.