import time

from src.benchmark.logger import BenchmarkLogger
from src.core.ollama_client import OllamaClient


class BenchmarkRunner:
    def __init__(self, client: OllamaClient, logger: BenchmarkLogger):
        self.client = client
        self.logger = logger

    def run_benchmark(self, task_type: str, prompt: str, models: list[str]) -> list[dict]:
        """Run prompt against each model, collect ratings, compute scores, write CSV."""
        raw_results: list[dict] = []

        for model in models:
            print(f"\nRunning {model}...")
            start = time.time()
            try:
                response = self.client.chat(model, [{"role": "user", "content": prompt}])
                latency = time.time() - start
            except Exception as e:
                print(f"  ERROR: {e}")
                raw_results.append({"model": model, "error": str(e)})
                continue

            tps = round(len(response) / latency, 1) if latency > 0 else 0
            print(f"\n--- {model} response ({latency:.1f}s, {tps} chars/s) ---")
            print(response[:600])
            if len(response) > 600:
                print(f"  ... [{len(response) - 600} more chars]")
            print("-" * 60)

            try:
                rating_str = input(f"Rate this response 1-5 (quality): ").strip()
                quality = max(1, min(5, int(rating_str)))
            except (ValueError, EOFError):
                quality = 3

            self.logger.log(task_type, model, len(prompt), len(response), latency)
            raw_results.append({
                "model": model,
                "latency": latency,
                "chars_per_sec": tps,
                "response_length": len(response),
                "quality": quality,
            })

        # Normalise speed and token efficiency across models tested (0-1)
        valid = [r for r in raw_results if "error" not in r]
        if not valid:
            return raw_results

        min_lat = min(r["latency"] for r in valid)
        max_lat = max(r["latency"] for r in valid)
        min_len = min(r["response_length"] for r in valid)
        max_len = max(r["response_length"] for r in valid)

        scored: list[dict] = []
        for r in valid:
            lat_range = max_lat - min_lat or 1
            len_range = max_len - min_len or 1

            # Lower latency = better speed score
            speed_score = 1.0 - (r["latency"] - min_lat) / lat_range
            # Closer to median length = better token efficiency (penalise extremes)
            median_len = sorted(r2["response_length"] for r2 in valid)[len(valid) // 2]
            token_eff = 1.0 - abs(r["response_length"] - median_len) / len_range

            quality_norm = (r["quality"] - 1) / 4  # 1-5 → 0-1
            composite = round(quality_norm * 0.6 + speed_score * 0.25 + token_eff * 0.15, 4)
            scored.append({**r, "speed_score": round(speed_score, 4),
                           "token_eff": round(token_eff, 4), "composite_score": composite})

        scored.sort(key=lambda x: x["composite_score"], reverse=True)
        print("\n=== Benchmark Results (ranked) ===")
        for i, r in enumerate(scored, 1):
            print(f"  #{i} {r['model']:30s} score={r['composite_score']:.3f}  "
                  f"quality={r['quality']}  latency={r['latency']:.1f}s")

        return scored
