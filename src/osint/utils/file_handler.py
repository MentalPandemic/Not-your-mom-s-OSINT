from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


class FileHandler:
    """Centralized file I/O operations for CSV and JSON formats.

    This utility provides lightweight alternatives to pandas for file operations,
    ensuring compatibility with Termux (ARM architecture) and maintaining
    all CSV/JSON export functionality.
    """

    @staticmethod
    def write_csv(data: list[dict[str, Any]], filepath: Path) -> None:
        """Write data to a CSV file.

        Args:
            data: List of dictionaries to write. All dictionaries must have
                  the same keys which will be used as CSV headers.
            filepath: Path to the output CSV file.

        Raises:
            ValueError: If data is empty.
            IOError: If the file cannot be written.
        """
        if not data:
            raise ValueError("Cannot write empty data to CSV")

        filepath.parent.mkdir(parents=True, exist_ok=True)

        with filepath.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)

    @staticmethod
    def read_csv(filepath: Path) -> list[dict[str, Any]]:
        """Read data from a CSV file.

        Args:
            filepath: Path to the input CSV file.

        Returns:
            List of dictionaries representing each row in the CSV file.

        Raises:
            FileNotFoundError: If the file does not exist.
            IOError: If the file cannot be read.
        """
        with filepath.open("r", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    @staticmethod
    def write_json(data: Any, filepath: Path) -> None:
        """Write data to a JSON file.

        Args:
            data: Data to serialize (must be JSON-serializable or have
                  objects with to_dict() methods).
            filepath: Path to the output JSON file.

        Raises:
            IOError: If the file cannot be written.
            TypeError: If data is not JSON-serializable.
        """
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Convert objects with to_dict() methods
        def _serialize(obj: Any) -> Any:
            if hasattr(obj, "to_dict") and callable(getattr(obj, "to_dict")):
                return obj.to_dict()
            return str(obj)

        content = json.dumps(data, indent=2, sort_keys=True, default=_serialize)

        filepath.write_text(content + "\n", encoding="utf-8")

    @staticmethod
    def read_json(filepath: Path) -> Any:
        """Read data from a JSON file.

        Args:
            filepath: Path to the input JSON file.

        Returns:
            Parsed JSON data (dict, list, or other JSON-compatible type).

        Raises:
            FileNotFoundError: If the file does not exist.
            json.JSONDecodeError: If the file contains invalid JSON.
            IOError: If the file cannot be read.
        """
        return json.loads(filepath.read_text(encoding="utf-8"))

    @staticmethod
    def to_dict_list(data: Any) -> list[dict[str, Any]]:
        """Convert data to a list of dictionaries.

        Args:
            data: Data to convert. Can be a list of objects with to_dict()
                  methods, or already a list of dictionaries.

        Returns:
            List of dictionaries.

        Examples:
            >>> FileHandler.to_dict_list([QueryResult(...), QueryResult(...)])
            [{'username': 'john', ...}, {...}]
        """
        result: list[dict[str, Any]] = []

        for item in data:
            if hasattr(item, "to_dict") and callable(getattr(item, "to_dict")):
                result.append(item.to_dict())
            elif isinstance(item, dict):
                result.append(item)
            else:
                raise ValueError(
                    f"Cannot convert {type(item).__name__} to dict. "
                    "Items must have to_dict() method or be dict objects."
                )

        return result
