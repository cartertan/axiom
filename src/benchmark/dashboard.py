"""Generate a benchmark HTML dashboard from benchmark_results.csv."""
import csv
import json
import os
from collections import defaultdict

import yaml

_CSV_PATH = "data/benchmarks/benchmark_results.csv"
_HTML_OUT = "reports/benchmark_dashboard.html"
_YAML_OUT = "config/models_recommended.yaml"


def _read_csv() -> list[dict]:
    if not os.path.exists(_CSV_PATH):
        return []
    with open(_CSV_PATH, newline="") as f:
        return list(csv.DictReader(f))


def _aggregate(rows: list[dict]) -> dict:
    """Return {model: {task_type: {avg_latency, avg_tps, count}}}."""
    data: dict = defaultdict(lambda: defaultdict(lambda: {"latencies": [], "tps": []}))
    for row in rows:
        model = row.get("model", "unknown")
        task = row.get("task_type", "GENERAL")
        try:
            data[model][task]["latencies"].append(float(row["latency_seconds"]))
            data[model][task]["tps"].append(float(row["tokens_per_second"]))
        except (ValueError, KeyError):
            pass

    result = {}
    for model, tasks in data.items():
        result[model] = {}
        for task, vals in tasks.items():
            lats = vals["latencies"]
            tps = vals["tps"]
            result[model][task] = {
                "avg_latency": round(sum(lats) / len(lats), 2) if lats else 0,
                "avg_tps": round(sum(tps) / len(tps), 1) if tps else 0,
                "count": len(lats),
            }
    return result


def _best_per_task(agg: dict) -> dict:
    """Return {task_type: best_model} based on lowest average latency."""
    task_models: dict = defaultdict(list)
    for model, tasks in agg.items():
        for task, stats in tasks.items():
            task_models[task].append((model, stats["avg_latency"]))
    return {
        task: min(entries, key=lambda x: x[1])[0]
        for task, entries in task_models.items()
        if entries
    }


def generate_dashboard(
    csv_path: str = _CSV_PATH,
    html_out: str = _HTML_OUT,
    yaml_out: str = _YAML_OUT,
) -> str:
    """Read benchmark CSV, write HTML dashboard + recommended YAML. Returns HTML path."""
    os.makedirs(os.path.dirname(html_out), exist_ok=True)
    rows = _read_csv()
    agg = _aggregate(rows)
    best = _best_per_task(agg)

    # Write recommended models YAML (separate from models.yaml — Carter reviews before merging)
    with open(yaml_out, "w") as f:
        yaml.dump(
            {"recommended_models_per_task": best,
             "generated_from": csv_path,
             "note": "Review and merge into config/models.yaml manually"},
            f, default_flow_style=False,
        )

    models = sorted(agg.keys())
    tasks = sorted({task for m in agg.values() for task in m})

    # Build chart datasets: one dataset per task, x-axis = models
    chart_datasets = []
    colours = ["#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f", "#edc948", "#b07aa1"]
    for i, task in enumerate(tasks):
        data_points = [agg.get(model, {}).get(task, {}).get("avg_tps", 0) for model in models]
        chart_datasets.append({
            "label": task,
            "data": data_points,
            "backgroundColor": colours[i % len(colours)],
        })

    table_rows_html = ""
    for model in models:
        for task in tasks:
            s = agg.get(model, {}).get(task)
            if s:
                table_rows_html += (
                    f"<tr><td>{model}</td><td>{task}</td>"
                    f"<td>{s['avg_latency']}s</td>"
                    f"<td>{s['avg_tps']}</td>"
                    f"<td>{s['count']}</td></tr>\n"
                )

    best_rows_html = "".join(
        f"<tr><td>{task}</td><td><strong>{model}</strong></td></tr>\n"
        for task, model in sorted(best.items())
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>AXIOM Benchmark Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<style>
  body {{ font-family: system-ui, sans-serif; margin: 2rem; background: #f9f9f9; color: #222; }}
  h1 {{ color: #2c3e50; }}
  h2 {{ color: #34495e; margin-top: 2rem; }}
  table {{ border-collapse: collapse; width: 100%; max-width: 900px; background: #fff; }}
  th, td {{ border: 1px solid #ddd; padding: 8px 12px; text-align: left; }}
  th {{ background: #2c3e50; color: #fff; }}
  tr:nth-child(even) {{ background: #f2f2f2; }}
  canvas {{ max-width: 900px; background: #fff; padding: 1rem; border-radius: 8px; }}
  .summary {{ background: #fff; padding: 1rem; border-radius: 8px; max-width: 600px; }}
</style>
</head>
<body>
<h1>AXIOM Benchmark Dashboard</h1>
<p>Generated from <code>{csv_path}</code> &mdash; {len(rows)} runs across {len(models)} models.</p>

<h2>Chars/s by Task &amp; Model</h2>
<canvas id="chart" height="120"></canvas>
<script>
new Chart(document.getElementById('chart'), {{
  type: 'bar',
  data: {{
    labels: {json.dumps(models)},
    datasets: {json.dumps(chart_datasets)}
  }},
  options: {{
    plugins: {{ legend: {{ position: 'top' }} }},
    scales: {{ y: {{ beginAtZero: true, title: {{ display: true, text: 'Chars / second (higher = faster)' }} }} }}
  }}
}});
</script>

<h2>Latency / Speed / Count per Model × Task</h2>
<table>
  <thead><tr><th>Model</th><th>Task</th><th>Avg Latency</th><th>Avg Chars/s</th><th>Runs</th></tr></thead>
  <tbody>{table_rows_html}</tbody>
</table>

<h2>Recommended Model per Task</h2>
<div class="summary">
  <table>
    <thead><tr><th>Task Type</th><th>Recommended Model</th></tr></thead>
    <tbody>{best_rows_html}</tbody>
  </table>
  <p><em>Based on lowest average latency. Quality ratings require interactive benchmark run.</em></p>
</div>
</body>
</html>"""

    with open(html_out, "w") as f:
        f.write(html)

    print(f"Dashboard written to {html_out}")
    print(f"Recommended models written to {yaml_out}")
    return html_out
