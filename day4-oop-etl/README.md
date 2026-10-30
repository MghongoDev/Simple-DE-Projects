# Day 4 - Object-Oriented ETL Framework

This project is a small ETL framework built from Python classes. It reads orders from a CSV file and users from a REST API, then validates, cleans, and writes the results to disk. Bad rows are saved with the reason they failed. If one source breaks, that pipeline fails on its own and the rest keep running.

Install the dependency, then run the main script:

```bash
cd day4-oop-etl
pip install -r requirements.txt
python main.py
```

Each run writes fresh files to `output/`, so re-running is safe.

## What it runs

`main()` builds three pipelines and runs them in order:

| Pipeline | Source | Destination |
|---|---|---|
| Orders Ingestion | `data/orders.csv` | `output/orders_clean.csv` |
| Users API Extraction | `jsonplaceholder.typicode.com/users` | `output/users_clean.json` |
| Broken Source | `data/does_not_exist.csv` | nothing useful, fails by design |

The third pipeline has no file to read. It shows the failure path: the run is marked FAILED, the other pipelines keep going, and the summary counts it.

Expected result: 25 orders extracted, 20 valid, 5 rejected. One rejected order is a duplicate `ORD-7004`. The API pipeline extracts and loads 10 users. The broken pipeline fails.

## Output files

| File | Contents |
|---|---|
| `output/orders_clean.csv` | valid orders with `line_total_kes` |
| `output/orders_rejected.csv` | excluded orders plus a `reasons` column, written only when some order was rejected |
| `output/users_clean.json` | valid API users with `id` renamed to `order_id` |

## How the code is organized

The framework lives in the `etl/` package. Each file has one job:

- **`errors.py`** — one exception hierarchy with `ETLError` at the root. The pipeline catches only the root, so new error types can be added without changing the pipeline code.
- **`extractors.py`** — `DataExtractor` is an abstract base class. Subclasses must implement `extract()`. `CSVExtractor` reads a file. `APIExtractor` calls a URL with a 10-second timeout. Both wrap every read failure in `ExtractionError`.
- **`transformer.py`** — `DataTransformer` checks each record against required fields, then parses numbers and emails. Valid records are cleaned. Invalid records are stored in `rejected_records` with a `reasons` field. The transformer does not raise on a bad row, because one bad row should not stop a pipeline.
- **`loader.py`** — `DataLoader` writes CSV or JSON, chosen by the destination file extension. An unsupported extension fails in `__init__`, before any work starts. `load()` returns the number of records written.
- **`main.py`** — `Pipeline` wires extractor, transformer, and loader together and runs the three phases. Each phase handles its own errors and updates a `RunSummary`, which the console prints.

The pipeline does not check what kind of extractor or loader it received. It calls the same methods either way. That is the point of the class design: the concrete source and destination are chosen in `main()`, not inside the pipeline.

## Validation rules for orders

An orders record is rejected when any of these is true:

- a required field is missing or blank. Required fields are `order_id`, `order_date`, `customer_email`, `city`, `quantity`, `unit_price_kes`.
- `customer_email` has no `@`.
- `quantity` is not a number, or is zero or less.
- `unit_price_kes` is not a number, or is zero or less.
- the record's primary key was already seen in this run. The first occurrence wins. Later rows are rejected as duplicates.

`quantity` and `unit_price_kes` may be written as strings with commas, such as `"1,150"`. The transformer strips the commas before parsing.

Cities are normalized to Title Case. Extra spaces are removed. Each clean order gets a `line_total_kes` column, which is quantity times unit price.

Rejected orders go to `output/orders_rejected.csv`. That file copies the original row and adds one `reasons` column. Today only the Orders pipeline writes rejected records.

## Design notes

- Adding a data source means adding one extractor subclass and one pipeline in `main()`. No other file changes.
- `DataLoader` supports `.csv` and `.json` only. Anything else raises `LoadingError` when the pipeline is built, not when it runs.
- `APIExtractor` expects the endpoint to return a JSON array. It rejects anything else, so the transformer never sees a shape it cannot loop over.
- `DataTransformer` is shared. Order-specific rules apply only when those fields are present, which is what keeps the users pipeline working through the same class.
- The rejected-records file is written only by the Orders pipeline. Giving another pipeline the same behavior is one flag, `Pipeline.WRITES_REJECTS`, not a fork of the loading path.
- `RunSummary.status` is `SUCCESS`, `PARTIAL`, or `FAILED`. `PARTIAL` means some records were rejected but the run still loaded data. `FAILED` means the source could not be read, nothing valid survived, or the destination could not be written.
