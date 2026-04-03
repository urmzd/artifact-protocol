Create a Rust HTTP API client library for a weather service.

Include:
- Types: WeatherResponse, Forecast, Location, Temperature, WindSpeed, Condition (enum)
- Client struct with reqwest, base URL, API key, timeout config
- Endpoint methods: current_weather, forecast (5-day), historical, search_location, alerts
- Custom error type with variants: HttpError, ParseError, RateLimited, InvalidApiKey, NotFound
- Builder pattern for client configuration
- Serde deserialization for all response types

Use section IDs: types, client, endpoints, error

Use AAP section markers to delineate each major code block.
Wrap each logical section with `<aap:section id="ID">` and `</aap:section>`.


Output raw code only. No markdown fences, no explanation.