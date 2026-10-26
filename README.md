# Duka Connect Analytics

This project is a small data engineering exercise for Duka Connect, Nairobi B2B distributor. The team needs customer data from a partner API in a flat, analysis-ready format so it can be joined with internal sales records.

## What is in this repo

The repository currently covers the first delivery of the pipeline:

- Day 1 API extraction: fetch data from a REST endpoint, inspect the structure, flatten nested JSON, and export a cleaned CSV.
- Output: a ready-to-use customer dataset in CSV format.

## Repo layout

- `day1-api-extraction/` - the working extraction pipeline
  - `extract_customers.py` - pulls customer data, flattens nested fields, and writes CSV output
  - `requirements.txt` - Python dependencies
  - `output/customers_clean.csv` - exported dataset

## Day 1 pipeline

The current script does a few core jobs:

1. Calls the JSONPlaceholder users API.
2. Validates the HTTP response and JSON payload.
3. Prints a quick view of the data structure.
4. Pulls the key customer fields needed for analysis.
5. Recursively flattens nested objects such as address and company data into column names like `address_city` and `company_name`.
6. Converts the flattened records into a pandas DataFrame and exports a cleaned CSV.

## Quick start

From the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r day1-api-extraction/requirements.txt
python day1-api-extraction/extract_customers.py
```

This writes the output to:

```text
day1-api-extraction/output/customers_clean.csv
```

## Notes

This is a first-pass, practical ETL flow. It is designed to prove the approach: pull the data, normalize it, and generate a clean CSV for downstream analysis.

