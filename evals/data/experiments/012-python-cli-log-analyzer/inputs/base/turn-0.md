Create a Python CLI log analyzer tool using argparse.

Include:
- Log parser that handles common formats (Apache, Nginx, JSON structured logs)
- Analysis functions: top IPs, status code distribution, response time percentiles, error rate over time, top endpoints
- Output formatters: table (rich-style ASCII), JSON, CSV
- Main function with argparse: input file, output format, time range filter, top-N limit
- Type hints throughout
