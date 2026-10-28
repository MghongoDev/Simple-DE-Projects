# Day 2 - Multi-File Data Processing Pipeline

## Project Overview
This pipeline ingests daily transaction CSV files from Soko Fresh Supermarkets, validates the data, handles schema changes, removes duplicates across files, and outputs a consolidated dataset alongside a report of rejected rows and a processing summary.

## Approach & Assumptions

### 1. The Unexpected Header (Column Alias)
**Decision:** Map the known alias.
On Day 3 (`transactions_2026-10-03.csv`), a POS upgrade changed the `quantity` column to `qty`. Instead of rejecting the entire Day 3 file (which would lose perfectly good sales data), the script implements a `COLUMN_ALIASES` dictionary in `read_transactions()`. It catches `qty` and maps it to `quantity` during ingestion. If an *unrecognised* column is missing, the whole file is rejected.

### 2. Duplicate IDs
**Decision:** Keep the first occurrence, reject subsequent ones.
The pipeline uses a global `seen_ids` set that persists across all files. As it reads files chronologically (sorted by filename), it keeps the first time it sees a `transaction_id`. Any future row with that ID is rejected with the reason `duplicate ID (TXN-xxxx)`. This applies to duplicates within the same file and retries across different days.

### 3. Data Cleaning and Formatting
- Values are `.strip()`-ed of whitespace.
- `quantity` and `unit_price` are cast to integers.
- `line_total` is calculated (`quantity * unit_price`).
- The script accounts for the missing `payment_ref` column gracefully. If a file lacks that column, it still parses successfully and outputs a blank value in the final CSV.

### 4. Rejected Records
The `rejected_transactions.csv` captures every row that fails validation. It prepends the `source_file` and `row_number` (starting at 2 for the first data row) so finance can easily locate the error in the original file. Reasons are joined by semicolons (e.g., `missing customer_id; invalid quantity (not a number)`).

## How to Run

1. Ensure you have Python 3.8+ installed.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt