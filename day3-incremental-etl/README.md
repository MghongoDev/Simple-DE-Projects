# Day 3 - Incremental ETL Pipeline

This pipeline loads JSON transaction batches from `incoming/` into a CSV warehouse at `data/transactions.csv`. It keeps a checkpoint so a batch is processed only once. It classifies each record and only writes newer updates.

It needs Python 3 and uses only the standard library.

## Run it

From the project folder:

```bash
python incremental_etl.py
```

Each run:

- reads unprocessed JSON batches from `incoming/`
- updates `data/transactions.csv`
- records processed batch IDs in `state/checkpoint.json`
- writes run details to `logs/etl.log`

Run the script twice in a row. The second run should change nothing.

Each run produces console output and appends the same lines to `logs/etl.log`.

### Terminal output from the first run

```
2026-11-03 01:52:19 INFO  Run started
2026-11-03 01:52:19 INFO  Existing rows loaded: 20
2026-11-03 01:52:19 INFO  Batch BATCH-2026-10-21-01: 17 records read
2026-11-03 01:52:19 INFO  New: 7 | Updated: 0 | Duplicates: 6 | Invalid: 4
2026-11-03 01:52:19 WARNING Invalid record MP-50008: older version (updated_at is not newer)
2026-11-03 01:52:19 WARNING Invalid record None: missing transaction_id
2026-11-03 01:52:19 WARNING Invalid record MP-50021: duplicate ID within batch
2026-11-03 01:52:19 WARNING Invalid record MP-50026: negative amount
2026-11-03 01:52:19 INFO  Rows after load: 27
2026-11-03 01:52:19 INFO  Run finished in 0.003s
```

### Terminal output from the second run

```
2026-11-03 01:52:19 INFO  Run started
2026-11-03 01:52:19 INFO  Existing rows loaded: 27
2026-11-03 01:52:19 INFO  Batch BATCH-2026-10-21-01 already processed - skipping
2026-11-03 01:52:19 INFO  Rows after load: 27
2026-11-03 01:52:19 INFO  Run finished in 0.003s
```

### Terminal output after deleting the checkpoint

```
2026-11-03 01:52:34 INFO  Run started
2026-11-03 01:52:34 INFO  Existing rows loaded: 27
2026-11-03 01:52:34 INFO  Batch BATCH-2026-10-21-01: 17 records read
2026-11-03 01:52:34 INFO  New: 0 | Updated: 0 | Duplicates: 13 | Invalid: 4
2026-11-03 01:52:34 WARNING Invalid record MP-50008: older version (updated_at is not newer)
2026-11-03 01:52:34 WARNING Invalid record None: missing transaction_id
2026-11-03 01:52:34 WARNING Invalid record MP-50021: duplicate ID within batch
2026-11-03 01:52:34 WARNING Invalid record MP-50026: negative amount
2026-11-03 01:52:34 INFO  Rows after load: 27
2026-11-03 01:52:34 INFO  Run finished in 0.003s
```

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

## Delete the checkpoint

To demonstrate that the pipeline starts fresh, delete `state/checkpoint.json` and run the script again.

```bash
rm state/checkpoint.json
python incremental_etl.py
```

The output above shows the checkpoint-delete run: it re-processed the batch, found no new rows, and kept 27 rows.

## Logs

`logs/etl.log` keeps one block per run. Each block records:

- when the run starts and ends
- how many existing rows were loaded
- per-batch counts of new, updated, duplicate, and invalid records
- invalid record IDs and reasons

The file is appended on every run, so it grows with each execution.

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

## Expected output

## state/checkpoint.json (shape)

{
  "last_run_at": "<ISO timestamp>",
  "processed_batches": ["<batch_id>", "..."],
  "high_watermark": "<latest updated_at loaded>",
  "row_count": <int>
}

## logs/etl.log (one block per run)

<timestamp> INFO  Run started
<timestamp> INFO  Existing rows loaded: <n>
<timestamp> INFO  Batch <batch_id>: <n> records read
<timestamp> INFO  New: <n> | Updated: <n> | Duplicates: <n> | Invalid: <n>
<timestamp> WARNING Invalid record <id or index>: <reason>
<timestamp> INFO  Rows after load: <n>
<timestamp> INFO  Run finished in <seconds>s

## A second run with no new batches

<timestamp> INFO  Batch <batch_id> already processed - skipping
<timestamp> INFO  New: 0 | Updated: 0 | Duplicates: 0 | Invalid: 0

## data/transactions.csv
Same columns as the input file, one row per transaction_id, sorted by transaction_id.
