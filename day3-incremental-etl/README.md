# Day 3 - Incremental ETL Pipeline

## Project Overview
This project implements an idempotent incremental ETL pipeline for Lipa Haraka. It ingests JSON batches of M-Pesa and Card transactions, compares them against the existing warehouse (a CSV file), classifies them, and safely updates the warehouse without duplicating data. 

The pipeline uses checkpoints to ensure that a previously processed batch is never processed again, preventing double-counting.

## Approach & Assumptions

### 1. Classification Rules
When processing a new batch, each transaction is placed into exactly one of four buckets:
- **Invalid**: The record is missing a `transaction_id`, has a negative amount, or has a non-numeric amount (e.g., `"3,450.00"` is handled, but `"abc"` is invalid). Duplicates *within the same batch file* are also rejected as invalid to prevent internal conflicts.
- **New**: The `transaction_id` does not exist in the current warehouse. It is inserted.
- **Duplicate**: The `transaction_id` exists, and the newly provided fields exactly match the fields already in the warehouse. It is ignored.
- **Updated**: The `transaction_id` exists, but fields differ. **Assumption**: To prevent out-of-order batch processing from overwriting newer data with older data, an update is only accepted if the `updated_at` timestamp of the incoming record is *strictly greater* than the `updated_at` timestamp in the warehouse. If it is older, it is classified as **Invalid** (with the reason `"older version"`).

### 2. Idempotency and Data Safety
- **Checkpoints**: The `state/checkpoint.json` file records which `batch_id`s have been successfully loaded. If the script is run twice, the second run sees the batch ID in the checkpoint and skips it entirely.
- **Atomic Writes**: Both `save_warehouse` and `write_checkpoint` use Python's `tempfile` and `shutil.move`. The data is written to a temporary file in the same directory first, and then atomically swapped with the real file. This guarantees that if the script crashes mid-write, the original file is not corrupted.
- **Order of Operations**: The pipeline writes the warehouse data first, then updates the checkpoint. If the script crashes between these two steps, the next run will reprocess the batch but find all records are now duplicates, resulting in no data corruption.

