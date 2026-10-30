"""Extractors are responsible for getting raw data from a source."""

from abc import ABC, abstractmethod
import csv
import requests
from typing import Any
from .errors import ExtractionError


class DataExtractor(ABC):
    """Common interface for every data source."""

    def __init__(self, source: str, name: str | None = None) -> None:
        self.source = source
        # use the provided name or use the class name as a default
        self.name = name if name else self.__class__.__name__

    @abstractmethod
    def extract(self) -> list[dict[str, Any]]:
        """Return the raw records from the source."""
        pass

    def __repr__(self) -> str:
        # Provide a clean string representation for logs and print statements.
        return f"{self.__class__.__name__}(source='{self.source}')"


class CSVExtractor(DataExtractor):
    """Reads records from a CSV file."""

    def extract(self) -> list[dict[str, Any]]:
        records = []
        try:
            with open(self.source, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    records.append(dict(row))
            return records
        except FileNotFoundError:
            # Wrap standard library errors in the custom ExtractionError
            raise ExtractionError(f"CSV file not found at path: {self.source}.")
        except Exception as e:
            raise ExtractionError(f"Failed to read CSV file: {e}")

    def __repr__(self) -> str:
        # Show specific source for CSV
        return f"CSVExtractor(file='{self.source}')"


class APIExtractor(DataExtractor):
    """Reads records from the JSON HTTP endpoint."""
    def __init__(self, source: str, name: str | None = None, timeout: float = 10.0) -> None:
        super().__init__(source, name)
        self.timeout = timeout

    def extract(self) -> list[dict[str, Any]]:
        try:
            response = requests.get(self.source, timeout=self.timeout)
            # Check for HTTP errors such as 404 or 500
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            # Catch network errors and raise custom error
            raise ExtractionError(f"API request failed: {e}")
        except ValueError:
            # Catch JSON decoding errors
            raise ExtractionError("API did not return valis JSON.")
