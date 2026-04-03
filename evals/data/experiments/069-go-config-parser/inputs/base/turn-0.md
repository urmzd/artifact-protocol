Create a Go configuration loader that reads from file, environment, and flags.

Include:
- Config struct with nested sub-configs: Server (host, port, timeout), Database (DSN, pool size, migrations), Redis (addr, password, DB), Logging (level, format, output)
- Loader: read YAML file, overlay with env vars (APP_ prefix), overlay with CLI flags
- Validation: required fields, port ranges, valid log levels, DSN format
- Defaults for all fields
