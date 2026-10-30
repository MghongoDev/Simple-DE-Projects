# Simple DE Projects

A portfolio of small Python projects that extract, clean, and prepare data for analysis. Each project has its own instructions, dependencies, and sample or output data.

## Projects

| Project | What it does | Status |
|---|---|---|
| [Day 1: API extraction](day1-api-extraction/) | Fetches customer records from JSONPlaceholder, flattens nested fields, and writes a CSV. | Runnable |
| [Day 2: Multi-file transaction pipeline](day2-multi-file-pipeline/) | Processes daily transaction CSVs, checks rows, handles the `qty` column change and duplicate IDs, and prepares accepted and rejected records. | Runnable |
| [Day 3: Incremental ETL pipeline](day3-incremental-etl/) | Loads JSON transaction batches into a CSV warehouse, classifies records, and tracks processed batches to prevent reprocessing. | Runnable |
| [Day 4: Object-oriented ETL framework](day4-oop-etl/) | Runs CSV and API pipelines through a small class-based ETL framework, validates and cleans records, writes rejected rows with reasons, and handles a broken source without crashing. | Runnable |

Day 1 shows HTTP requests, JSON handling, data cleaning, and CSV export. Day 2 processes daily sales files and reports accepted and rejected transactions. Day 3 applies newer transaction records from JSON batches and skips batches already recorded in its checkpoint. Day 4 wires extraction, transformation, and loading through shared classes and keeps the failure of one pipeline from stopping the rest.

## Run Day 1

Requirements: Python 3 and an internet connection to reach the JSONPlaceholder API.

From the repository root, create a virtual environment and install the project dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r day1-api-extraction/requirements.txt
```

Run the script from its project folder so it writes the CSV to the expected location:

```bash
cd day1-api-extraction
python extract_customers.py
```

The script saves the result to [day1-api-extraction/output/customers_clean.csv](day1-api-extraction/output/customers_clean.csv). See the [Day 1 README](day1-api-extraction/README.md) for implementation details.

## Run Day 2

Requirements: Python 3.8 or later. The pipeline uses only Python's standard library, so it needs no package installation.

From the repository root, run:

```bash
cd day2-multi-file-pipeline
python pipeline.py --input data/ --output output/
```

The pipeline writes accepted transactions to [day2-multi-file-pipeline/output/consolidated_transactions.csv](day2-multi-file-pipeline/output/consolidated_transactions.csv), rejected rows with reasons to [day2-multi-file-pipeline/output/rejected_transactions.csv](day2-multi-file-pipeline/output/rejected_transactions.csv), and run counts to [day2-multi-file-pipeline/output/summary.txt](day2-multi-file-pipeline/output/summary.txt). See the [Day 2 README](day2-multi-file-pipeline/README.md) for how validation and duplicate handling work.

## Run Day 3

Requirements: Python 3. The pipeline uses only the standard library, so it needs no package installation.

Run it from its project folder so the relative data, incoming, state, and logs paths resolve correctly:

```bash
cd day3-incremental-etl
python incremental_etl.py
```

The script reads unprocessed JSON batches from `incoming/`, updates [day3-incremental-etl/data/transactions.csv](day3-incremental-etl/data/transactions.csv), records processed batch IDs in [day3-incremental-etl/state/checkpoint.json](day3-incremental-etl/state/checkpoint.json), and writes run details to [day3-incremental-etl/logs/etl.log](day3-incremental-etl/logs/etl.log). It rejects invalid records and older updates, ignores exact duplicates, and accepts updates only when their `updated_at` timestamp is newer. See the [Day 3 README](day3-incremental-etl/README.md) for the classification rules and write-safety details.

## Run Day 4

Requirements: Python 3 and the `requests` package.

From the repository root, install the dependency and run the framework:

```bash
cd day4-oop-etl
pip install -r requirements.txt
python main.py
```

The framework runs three pipelines in order:

- Orders Ingestion reads `data/orders.csv` and writes `output/orders_clean.csv`.
- Users API Extraction calls `https://jsonplaceholder.typicode.com/users` and writes `output/users_clean.json`.
- Broken Source tries to read `data/does_not_exist.csv` and fails by design.

Each run writes fresh files to `output/`, so re-running is safe.

Expected result: 25 orders extracted, 20 valid, 5 rejected. One rejected order is a duplicate `ORD-7004`. The API pipeline extracts and loads 10 users. The broken pipeline fails.

The Orders pipeline also writes `output/orders_rejected.csv` when it rejects rows. That file copies the original order and adds a `reasons` column. Only the Orders pipeline writes rejected records today.

See the [Day 4 README](day4-oop-etl/README.md) for the framework layout, validation rules, and design notes.

## Repository layout

```text
Simple-DE-Projects/
├── README.md
├── day1-api-extraction/
│   ├── README.md
│   ├── extract_customers.py
│   ├── requirements.txt
│   └── output/
│       └── customers_clean.csv
├── day2-multi-file-pipeline/
│   ├── README.md
│   ├── pipeline.py
│   ├── requirements.txt
│   ├── test_pipeline.py
│   ├── data/
│   │   └── transactions_2026-10-*.csv
│   └── output/
│       ├── consolidated_transactions.csv
│       ├── rejected_transactions.csv
│       └── summary.txt
├── day3-incremental-etl/
│   ├── README.md
│   ├── incremental_etl.py
│   ├── requirements.txt
│   ├── data/
│   │   └── transactions.csv
│   ├── incoming/
│   │   └── batch_*.json
│   ├── logs/
│   │   └── etl.log
│   └── state/
│       └── checkpoint.json
└── day4-oop-etl/
    ├── README.md
    ├── main.py
    ├── requirements.txt
    ├── data/
    │   └── orders.csv
    ├── etl/
    │   ├── __init__.py
    │   ├── errors.py
    │   ├── extractors.py
    │   ├── transformer.py
    │   └── loader.py
    └── output/
        ├── orders_clean.csv
        ├── orders_rejected.csv
        └── users_clean.json
```

Each project keeps its own README and `requirements.txt`. Follow those files when setting up or running a project.
