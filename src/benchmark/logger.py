import csv
import os
from collections import defaultdict
from datetime import datetime, timezone

_CSV_PATH = "data/benchmarks/benchmark_results.csv"
_FIELDNAMES = [
    "timestamp",
    "task_type",
    "model",
    "prompt_chars",
    "response_chars",
    "latency_seconds",
    "tokens_per_second",
]


class BenchmarkLogger:
    def __init__(self, csv_path: str = _CSV_PATH):
        self._path = csv_path
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    def log(
        self,
        task_type: str,
        model: str,
        prompt_length: int,
        response_length: int,
        latency_seconds: float,
    ) -> None:
        """Append a benchmark row to the CSV, creating the file with headers if needed."""
        tps = round(response_length / latency_seconds, 2) if latency_seconds > 0 else 0.0
        row = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "task_type": task_type,
            "model": model,
            "prompt_chars": prompt_length,
            "response_chars": response_length,
            "latency_seconds": round(latency_seconds, 3),
            "tokens_per_second": tps,
        }
        file_exists = os.path.exists(self._path)
        with open(self._path, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=_FIELDNAMES)
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)

    def get_summary(self) -> dict:
        """Return {model: {task_type: avg_latency}} from the CSV."""
        if not os.path.exists(self._path):
            return {}

        totals: dict = defaultdict(lambda: defaultdict(list))
        with open(self._path, newline="") as f:
            for row in csv.DictReader(f):
                model = row["model"]
                task = row["task_type"]
                try:
                    totals[model][task].append(float(row["latency_seconds"]))
                except ValueError:
                    pass

        return {
            model: {
                task: round(sum(lats) / len(lats), 3)
                for task, lats in tasks.items()
            }
            for model, tasks in totals.items()
        }
