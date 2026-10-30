"""The loader is responsible for writing data to files."""
import csv
import json
from pathlib import Path
from typing import Any
from .errors import ETLError


class DataLoader:
    """Writes transformed resordc to a destination file(CSV or JSON by extension)."""

    def __init__(self, destination: Path) -> None:
        self.destination = Path(destination)
        # Check the file extension at construction time to fail test f it's unsupported
        if self.destination.suffix.lower() not in [".csv", ".json"]:
            raise ETLError(f"Unsupported file extension: {self.destination.suffix}. Use .csv or .json")

    def load(self, records: list[dict[str, Any]]) -> int:
        """Write the records and return how many were written."""
        if not records:
            return 0

        # Ensure the output directory exists
        self.destination.parent.mkdir(parents=True, exist_ok=True)

        if self.destination.suffix.lower() == ".csv":
            return self._write_csv(records)
        elif self.destination.suffix.lower() == ".json":
            return self._write_json(records)

    def _write_csv(self, records: list[dict[str, Any]]) -> int:
        # Get headers from the first record assuming all records have the same keys
        fieldnames = list(records[0].keys())

        with open(self.destination, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)

        return len(records)

    def _write_json(self, records: list[dict[str, Any]]) -> int:
        with open(self.destination, mode="w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)

        return len(records)