"""
Day 3 - Incremental ETL Pipeline
Squad Python Specialization - Data Engineering

Run it twice in a row. The second run must change nothing.
"""
import csv
import json
import logging
import time
from datetime import datetime
from pathlib import Path

# File paths based on the project structure
WAREHOUSE_PATH = Path("data") / "transactions.csv"
BATCH_DIR = Path("incoming")
CHECKPOINT_PATH = Path("state") / "checkpoint.json"
LOG_PATH = Path("logs") / "etl.log"

KEY = "transaction_id"
COMPARED_FIELDS = ("customer_id", "merchant", "amount_kes", "status", "channel", "updated_at")


def setup_logging(path: Path = LOG_PATH) -> logging.Logger:
    """Configure a logger that writes to both the console and a log file."""
    # Create the logs folder if it doesn't exist
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Get the logger
    logger = logging.getLogger("ETL_Logger")
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers to prevent duplicate logs if run multiple times
    if logger.hasHandlers():
        logger.handlers.clear()
        
    # Define the log format
    formatter = logging.Formatter('%(asctime)s %(levelname)-5s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    
    # 1. Define console handler that prints to the terminal
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 2. Define file handler that appends to the log file
    file_handler = logging.FileHandler(path, mode='a', encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger


def load_existing(path: Path = WAREHOUSE_PATH) -> dict[str, dict]:
    """Read the loaded transactions into a dict keyed by transaction_id."""
    # Initialize empty existing dictionary
    existing = {}
    
    # If the file doesn't exist yet, return an empty dictionary
    if not path.exists():
        return existing
        
    # Open and read the CSV file
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            txn_id = row[KEY]
            
            # Convert amount to float so it can be compared properly later
            if row.get("amount_kes"):
                row["amount_kes"] = float(row["amount_kes"])
                
            existing[txn_id] = row
            
    return existing


def load_batch(path: Path) -> tuple[str, list[dict]]:
    """Read one JSON batch file and return (batch_id, transactions)."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            batch_id = data.get("batch_id", "UNKNOWN")
            transactions = data.get("transactions", [])
            return batch_id, transactions
    except Exception as e:
        # If the JSON is malformed, log the error and return empty values
        logging.error(f"Failed to read batch {path.name}: {e}")
        return None, []


def validate_record(record: dict) -> list[str]:
    """Return the reasons a batch record cannot be loaded (empty list means valid)."""
    # Initialize empty reasons list
    reasons = []
    
    # 1. Check if transaction_id is missing
    if not record.get(KEY):
        reasons.append("missing transaction_id")
        
    # 2. Check the amount
    amount = record.get("amount_kes")
    if amount is not None:
        try:
            # If it's a string with commas e.g "2,790.00", remove commas first
            if isinstance(amt, str):
                amount = amount.replace(",", "")
                
            val = float(amount)
            
            # Check for negative numbers
            if val < 0:
                reasons.append("negative amount")
        except ValueError:
            # If the float conversion fails, it's not a number
            reasons.append("invalid amount (not a number)")
    else:
        reasons.append("missing amount")
        
    return reasons


def classify(existing: dict[str, dict], batch: list[dict]) -> dict[str, list[dict]]:
    """Split the batch into the buckets 'new', 'updated', 'duplicate' and 'invalid'."""
    # Initialize buckets dictionary
    buckets = {
        "new": [], 
        "updated": [], 
        "duplicate": [], 
        "invalid": []
    }
    
    # Keep track of IDs seen in this specific batch to catch internal duplicates
    batch_seen_ids = set()
    
    for record in batch:
        # 1. Check if the record has validation errors
        problems = validate_record(record)
        if problems:
            # Join the errors with a semicolon
            record["_reasons"] = "; ".join(problems)
            buckets["invalid"].append(record)
            continue
            
        txn_id = record[KEY]
        
        # 2. Check for duplicates within the batch itself
        if txn_id in batch_seen_ids:
            record["_reasons"] = "duplicate ID within batch"
            buckets["invalid"].append(record)
            continue
            
        # Add this ID to the batch tracker
        batch_seen_ids.add(txn_id)
        
        # 3. Compare with the existing warehouse data
        if txn_id not in existing:
            # Append ompletely new transaction
            buckets["new"].append(record)
        else:
            old_record = existing[txn_id]
            is_identical = True
            
            # Check every field to see if anything changed
            for field in COMPARED_FIELDS:
                old_val = str(old_record.get(field, ""))
                new_val = str(record.get(field, ""))
                
                # Handle amount formatting by standardizing num of decimal places
                if field == "amount_kes":
                    if old_val:
                        old_val = f"{float(old_val):.2f}"
                    if new_val:
                        # Clean commas before converting
                        clean_new = new_val.replace(",", "")
                        new_val = f"{float(clean_new):.2f}"
                        
                # If any field is different, it's not a duplicate
                if old_val != new_val:
                    is_identical = False
                    break
                    
            if is_identical:
                buckets["duplicate"].append(record)
            else:
                # It's different, so check timestamps.
                old_time = old_record.get("updated_at", "")
                new_time = record.get("updated_at", "")
                
                if new_time > old_time:
                    buckets["updated"].append(record)
                else:
                    # It's different, but older data so reject to avoid overwriting.
                    record["_reasons"] = "older version (updated_at is not newer)"
                    buckets["invalid"].append(record)
                    
    return buckets


def upsert(existing: dict[str, dict], new: list[dict], updated: list[dict]) -> dict[str, dict]:
    """Return the merged state: inserts for new keys, replacements for updated keys."""
    # Make a copy of the existing data so original isn't modified while looping
    merged_state = dict(existing)
    
    # Add new records
    for record in new:
        # Ensure amount is a clean number
        if isinstance(record["amount_kes"], str):
             record["amount_kes"] = record["amount_kes"].replace(",", "")
        merged_state[record[KEY]] = record
        
    # Replace updated records
    for record in updated:
        if isinstance(record["amount_kes"], str):
             record["amount_kes"] = record["amount_kes"].replace(",", "")
        merged_state[record[KEY]] = record
        
    return merged_state


def read_checkpoint(path: Path = CHECKPOINT_PATH) -> dict:
    """Return the saved checkpoint, or a fresh one if none exists yet."""
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            # If the file is corrupt, start fresh
            pass
            
    # Default starting checkpoint
    return {
        "last_run_at": None,
        "processed_batches": [],
        "high_watermark": None,
        "row_count": 0
    }


def write_checkpoint(checkpoint: dict, path: Path = CHECKPOINT_PATH) -> None:
    """Persist the checkpoint so an interrupted run never leaves a half-written file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to a temporary file first
    temp_path = str(path) + ".tmp"
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f, indent=2)
        
    # Rename the temp file to the real filename to overwrite the old one safely
    Path(temp_path).replace(path)


def save_warehouse(state: dict[str, dict], path: Path = WAREHOUSE_PATH) -> None:
    """Write the merged state back to CSV in a stable order."""
    path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = [KEY] + list(COMPARED_FIELDS)
    
    # Write to a temporary file first
    temp_path = str(path) + ".tmp"
    
    with open(temp_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        # Get all keys and sort them alphabetically
        sorted_keys = sorted(state.keys())
        
        for txn_id in sorted_keys:
            row = state[txn_id]
            # Create a clean dictionary with only the wanted fields
            clean_row = {}
            for key in fieldnames:
                clean_row[key] = row.get(key)
                
            writer.writerow(clean_row)
            
    # Rename the temp file to the real filename
    Path(temp_path).replace(path)


def run() -> dict:
    """Process every batch not yet recorded in the checkpoint and return run statistics."""
    logger = setup_logging()
    start_time = time.time()
    
    logger.info("Run started")
    
    # 1. Load existing data and checkpoint
    existing_data = load_existing()
    checkpoint = read_checkpoint()
    
    logger.info(f"Existing rows loaded: {len(existing_data)}")
    
    # Track totals for this run
    total_new = 0
    total_updated = 0
    total_dups = 0
    total_invalid = 0
    batches_processed = []
    
    # 2. Find all JSON files
    if BATCH_DIR.exists():
        batch_files = sorted(list(BATCH_DIR.glob("*.json")))
    else:
        batch_files = []
        
    # 3. Process each batch
    for file_path in batch_files:
        batch_id, transactions = load_batch(file_path)
        
        # Skip if batch couldn't be loaded
        if not batch_id:
            continue
            
        # Skip if batch already processed according to the checkpoint
        if batch_id in checkpoint["processed_batches"]:
            logger.info(f"Batch {batch_id} already processed - skipping")
            continue
            
        logger.info(f"Batch {batch_id}: {len(transactions)} records read")
        
        # Classify the records
        buckets = classify(existing_data, transactions)
        
        n_new = len(buckets["new"])
        n_upd = len(buckets["updated"])
        n_dup = len(buckets["duplicate"])
        n_inv = len(buckets["invalid"])
        
        total_new += n_new
        total_updated += n_upd
        total_dups += n_dup
        total_invalid += n_inv
        
        logger.info(f"New: {n_new} | Updated: {n_upd} | Duplicates: {n_dup} | Invalid: {n_inv}")
        
        # Log out the invalid records
        for inv in buckets["invalid"]:
            id_val = inv.get(KEY, "unknown")
            reason = inv.get("_reasons", "unknown error")
            logger.warning(f"Invalid record {id_val}: {reason}")
            
        # Apply the changes to in-memory dictionary
        existing_data = upsert(existing_data, buckets["new"], buckets["updated"])
        batches_processed.append(batch_id)
        
    # 4. Save the data file FIRST
    save_warehouse(existing_data)
    logger.info(f"Rows after load: {len(existing_data)}")
    
    # 5. Update and write checkpoint ONLY IF data save succeeded
    if batches_processed:
        # Add the new batches to the checkpoint
        for b in batches_processed:
            checkpoint["processed_batches"].append(b)
            
        checkpoint["last_run_at"] = datetime.now().isoformat()
        checkpoint["row_count"] = len(existing_data)
        
        # Find the newest updated_at timestamp across all rows
        newest_time = ""
        for row in existing_data.values():
            row_time = row.get("updated_at", "")
            if row_time > newest_time:
                newest_time = row_time
                
        checkpoint["high_watermark"] = newest_time
        
        write_checkpoint(checkpoint)
        
    # 6. Calculate time taken
    elapsed = round(time.time() - start_time, 3)
    logger.info(f"Run finished in {elapsed}s")
    
    return {
        "new": total_new, 
        "updated": total_updated, 
        "duplicates": total_dups, 
        "invalid": total_invalid
    }


if __name__ == "__main__":
    run()