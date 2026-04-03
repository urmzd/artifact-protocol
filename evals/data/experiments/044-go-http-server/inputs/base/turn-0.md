Create a Go HTTP server for a URL shortener service using net/http.

Include:
- Types: URL struct, CreateRequest, StatsResponse, in-memory store with sync.RWMutex
- Handlers: CreateShortURL (POST), RedirectURL (GET /:code), GetStats (GET /stats/:code), ListURLs (GET /urls), DeleteURL (DELETE /:code)
- Middleware: logging, CORS, rate limiting (token bucket), request ID
- Server setup: routes, graceful shutdown, configuration from environment
- JSON encoding/decoding, proper HTTP status codes

Use section IDs: types, handlers, middleware, server

Use AAP section markers to delineate each major code block.
Wrap each logical section with `<aap:section id="ID">` and `</aap:section>`.


Output raw code only. No markdown fences, no explanation.