Create a Python web scraper for collecting product data from an e-commerce site.

Include:
- Config dataclass with base URL, rate limit, retry settings, output path
- Fetcher with retries, rate limiting, session management, and User-Agent rotation
- HTML parser extracting: product name, price, rating, review count, availability, image URL
- Storage layer writing to JSON Lines and SQLite
- Proper error handling and logging throughout
