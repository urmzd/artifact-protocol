Create a Python ETL data pipeline for processing CSV sales data.

Include:
- Extraction: read CSV files, handle encoding issues, parse dates
- Transformation: clean column names, calculate derived metrics (profit margin, YoY growth), categorize products, aggregate by region
- Validation: schema validation with expected types, null checks, range checks, duplicate detection
- Loading: write to Parquet and JSON, generate summary statistics
- Use dataclasses for pipeline config, pandas for data processing
