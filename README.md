# Simple DE Projects

A portfolio of small Python projects about extracting, cleaning, and preparing data for analysis. Each project has its own instructions, dependencies, and sample or output data.

## Projects

| Project | What it does | Status |
|---|---|---|
| [Day 1: API extraction](day1-api-extraction/README.md) | Fetches customer records from JSONPlaceholder, flattens nested fields, and writes a CSV. | Runnable |
| [Day 2: Multi-file transaction pipeline](day2-multi-file-pipeline/) | Processes Soko Fresh daily transaction CSVs, checks rows, handles the `qty` column change and duplicate IDs, and prepares accepted and rejected records. | Runnable |

The Day 1 project demonstrates HTTP requests, JSON handling, data cleaning, and CSV export. Day 2 processes daily sales files and reports both accepted and rejected transactions.

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

The pipeline writes accepted transactions to `output/consolidated_transactions.csv`, rejected rows with reasons to `output/rejected_transactions.csv`, and run counts to `output/summary.txt`. See the [Day 2 README](day2-multi-file-pipeline/README.md) for how validation and duplicate handling work.

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
└── day2-multi-file-pipeline/
    ├── README.md
    ├── pipeline.py
    ├── requirements.txt
    ├── test_pipeline.py
    ├── data/
    │   └── transactions_2026-10-*.csv
    └── output/
        ├── consolidated_transactions.csv
        ├── rejected_transactions.csv
        └── summary.txt
```

Each project keeps its own README and `requirements.txt`. Follow those files when setting up or running a project.
