# Day 1 - API Data Extraction

This script pulls user records from the JSONPlaceholder REST API, flattens the nested JSON, and writes one clean CSV.

It writes `output/customers_clean.csv`. The script needs Python 3 and an internet connection to reach the API.

## Run it

Install the dependencies from the project folder:

```bash
cd day1-api-extraction
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

Run the script:

```bash
python extract_customers.py
```

The script saves the result to `output/customers_clean.csv`.

## Procedure

1. Open a terminal in `day1-api-extraction/`.
2. Create and activate a virtual environment:
   - `python3 -m venv .venv`
   - `. .venv/bin/activate`
3. Install the dependencies:
   - `pip install -r requirements.txt`
4. Run the script:
   - `python extract_customers.py`
5. Check the output:
   - open `output/customers_clean.csv`
   - or run `ls -la output/` to confirm the file was written

If the API is unreachable, the script prints an error and exits without writing the CSV.

## What it does

1. Fetches users from `https://jsonplaceholder.typicode.com/users`.
2. Prints the shape of the response for reference.
3. Extracts core fields: id, name, email, city, and company name.
4. Builds a few in-memory structures (a names list, an id/email tuple list, and an id-to-city map).
5. Flattens every nested field, for example `address.city` becomes `address_city`.
6. Writes a DataFrame to CSV with the columns in a fixed order and renamed ids (`customer_id`).

## Error handling

`fetch_users` catches connection failures, timeouts, non-200 responses, and bad JSON. On failure it prints a clear message and exits with code 1 instead of raising a raw traceback.

## Notes

- Nested fields are flattened recursively, so new nesting depths work without code changes.
- Missing city or company defaults to `"Unknown"`.
- Latitude and longitude are written as floats.
- The output folder is created automatically if it does not exist.
