# Day 2 - Multi-File Transaction Pipeline

This pipeline reads daily transaction CSV files from Soko Fresh, checks them, and writes two results: a consolidated file of accepted rows and a file of rejected rows with reasons. It also writes a short text summary of the run.

It needs Python 3.8 or later and uses only the standard library.

## Run it

From the project folder:

```bash
cd day2-multi-file-pipeline
python pipeline.py --input data/ --output output/
```

The pipeline writes:

- `output/consolidated_transactions.csv` — accepted transactions
- `output/rejected_transactions.csv` — rejected rows and why
- `output/summary.txt` — run counts and totals

## Procedure

1. Open a terminal in `day2-multi-file-pipeline/`.
2. Confirm the input files exist in `data/`.
3. Run the pipeline:
   - `python pipeline.py --input data/ --output output/`
4. Read the console output for the run summary.
5. Check the output files:
   - `output/consolidated_transactions.csv`
   - `output/rejected_transactions.csv`
   - `output/summary.txt`

If you want a different output folder, change the `--output` path. If you want a different input folder, change the `--input` path.

## What it checks

For each row, the pipeline looks for:

- missing values in any required column
- quantity and unit price that are not positive numbers
- a transaction ID that has already appeared earlier in the run

Required columns are: `transaction_id`, `date`, `branch`, `customer_id`, `product`, `quantity`, `unit_price`, `payment_method`.

A row is rejected if any of those checks fail. Rejected rows keep their source file and row number so you can find them in the original file.

## The Day 3 header change

On 2026-10-03 the POS system renamed `quantity` to `qty`. The pipeline maps `qty` to `quantity` when it reads a file, so that day's data still loads. If a required column is missing and there is no known alias for it, the whole file is skipped.

## Duplicate handling

The pipeline keeps a set of transaction IDs it has already seen. The first time it sees an ID, the row is accepted. Any later row with the same ID is rejected as a duplicate. This applies inside one file and across files.

Files are processed in filename order, which matches the daily order.

## Cleaning

For accepted rows, the pipeline:

- strips whitespace from text fields
- converts `quantity` and `unit_price` to integers
- adds `line_total`, which is quantity times unit price

If a file is missing `payment_ref`, the pipeline still writes the row and leaves that field blank.

## Rejected rows file

`rejected_transactions.csv` includes the source file, row number, transaction ID, and a `reasons` column. Reasons are joined with semicolons, for example `missing customer_id; invalid quantity (not a number)`.

## Summary file

`summary.txt` shows:

- how many files were found and processed
- how many files had column issues
- how many rows were read, accepted, and rejected
- a breakdown of rejection reasons
- total revenue in KES
- the time the run finished
