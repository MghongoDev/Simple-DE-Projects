# Day 3 - Incremental ETL Pipeline

This pipeline loads JSON transaction batches from `incoming/` into a CSV warehouse at `data/transactions.csv`. It keeps a checkpoint so a batch is processed only once. It classifies each record and only writes newer updates.

It needs Python 3 and uses only the standard library.

## Run it

From the project folder:

```bash
cd day3-incremental-etl
python incremental_etl.py
```

Each run:

- reads unprocessed JSON batches from `incoming/`
- updates `data/transactions.csv`
- records processed batch IDs in `state/checkpoint.json`
- writes run details to `logs/etl.log`

Run the script twice in a row. The second run should change nothing.

## Procedure

1. Open a terminal in `day3-incremental-etl/`.
2. Confirm the warehouse file and checkpoint exist or can be created:
   - `data/transactions.csv`
   - `state/checkpoint.json`
3. Confirm the incoming batches are in `incoming/`.
4. Run the pipeline:
   - `python incremental_etl.py`
5. Read the console output for the run summary.
6. Check the results:
   - `data/transactions.csv` for updated warehouse rows
   - `state/checkpoint.json` for processed batch IDs
   - `logs/etl.log` for the run log

If you run the pipeline again with no new batches, it should skip every batch and write nothing new.

## Classification

Each incoming record lands in one of four buckets:

- **Invalid** — missing `transaction_id`, negative amount, non-numeric amount, or a duplicate ID inside the same batch file.
- **New** — the `transaction_id` is not in the warehouse yet.
- **Duplicate** — the `transaction_id` exists and the key fields match exactly.
- **Updated** — the `transaction_id` exists and the key fields differ, and the incoming `updated_at` is newer than the warehouse `updated_at`.

If an incoming record differs from the warehouse but has an older `updated_at`, the pipeline treats it as invalid. This stops an older batch from overwriting newer data.

For amount comparison, the pipeline normalizes decimal places before comparing.

## Checkpoint

`state/checkpoint.json` stores which `batch_id` values have already been processed. If a batch ID is in the checkpoint, the pipeline skips that file on the next run. This prevents double counting.

The checkpoint also stores:

- when the last run finished
- how many rows are in the warehouse
- the newest `updated_at` seen so far

If the checkpoint file is corrupt or missing, the pipeline starts fresh.

## Write safety

The pipeline writes the warehouse and the checkpoint with temporary files first, then replaces the real file. This reduces the chance of a half-written file if the script crashes.

The warehouse is written before the checkpoint is updated. If the script crashes between those two steps, the next run reprocesses the batch, but the records will already be in the warehouse, so the result is still correct.

## Logging

The pipeline logs to the console and to `logs/etl.log`. It records:

- when the run starts and ends
- how many existing rows were loaded
- per-batch counts of new, updated, duplicate, and invalid records
- invalid record IDs and reasons

## Data format

The warehouse uses these columns:

- `transaction_id`
- `customer_id`
- `merchant`
- `amount_kes`
- `status`
- `channel`
- `updated_at`

Incoming amounts may be numbers or strings with commas, such as `"3,450.00"`. The pipeline handles both.

## Notes

- A batch file must contain a `batch_id` and a `transactions` array.
- If a batch file is malformed JSON, the pipeline logs the error and skips it.
- The pipeline compares these fields when deciding whether a record changed: `customer_id`, `merchant`, `amount_kes`, `status`, `channel`, `updated_at`.
