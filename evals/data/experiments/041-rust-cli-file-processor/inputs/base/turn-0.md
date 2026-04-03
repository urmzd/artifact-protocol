Create a Rust CLI tool for processing and analyzing CSV files using clap and serde.

Include:
- CLI argument parsing with clap derive: input file, output format (table/json/csv), columns to select, filter expression, sort column, limit
- CSV processor: read file, parse headers, apply column selection, filtering, sorting, aggregation (count, sum, avg, min, max by group)
- Output formatters: pretty table, JSON, CSV
- Unit tests for parsing and filtering logic
- Proper error handling with thiserror
