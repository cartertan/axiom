import time
from typing import Callable

from src.benchmark.logger import BenchmarkLogger
from src.core.ollama_client import OllamaClient


class Orchestrator:
    def __init__(self, client: OllamaClient, benchmark: BenchmarkLogger):
        self.client = client
        self.benchmark = benchmark

    def _call(
        self,
        model: str,
        task_type: str,
        messages: list,
        progress_cb: Callable[[str], None] | None = None,
    ) -> tuple[str, float]:
        if progress_cb:
            progress_cb(model)
        start = time.time()
        response = self.client.chat(model, messages)
        latency = time.time() - start
        self.benchmark.log(task_type, model, sum(len(m["content"]) for m in messages), len(response), latency)
        return response, latency

    def run_ensemble(
        self,
        task_type: str,
        prompt: str,
        models: list[str],
        synthesiser_model: str,
        progress_cb: Callable[[str], None] | None = None,
    ) -> dict:
        individual_responses: list[dict] = []
        timings: dict[str, float] = {}

        for model in models:
            response, latency = self._call(
                model,
                task_type,
                [{"role": "user", "content": prompt}],
                progress_cb,
            )
            individual_responses.append({"model": model, "response": response})
            timings[model] = latency

        assembled = "\n\n".join(
            f"--- {r['model']} ---\n{r['response']}" for r in individual_responses
        )
        synth_prompt = (
            f"You are a synthesis expert. Below are responses from {len(models)} different AI models "
            f"to the same question. Produce a single best answer that combines their strengths, "
            f"resolves any contradictions, and is better than any individual response.\n\n"
            f"Original question:\n{prompt}\n\n"
            f"Model responses:\n{assembled}\n\n"
            f"Synthesised best answer:"
        )
        if progress_cb:
            progress_cb(f"{synthesiser_model} (synthesis)")
        synth_start = time.time()
        final = self.client.chat(synthesiser_model, [{"role": "user", "content": synth_prompt}])
        synth_latency = time.time() - synth_start
        self.benchmark.log(task_type, synthesiser_model, len(synth_prompt), len(final), synth_latency)
        timings[f"{synthesiser_model}(synthesis)"] = synth_latency

        return {
            "final": final,
            "individual_responses": individual_responses,
            "timings": timings,
        }

    def run_pipeline(
        self,
        task_type: str,
        prompt: str,
        model_sequence: list[str],
        progress_cb: Callable[[str], None] | None = None,
    ) -> dict:
        stages = ["draft", "refine", "polish"]
        stage_results: list[dict] = []
        timings: dict[str, float] = {}
        current_content = prompt

        for i, model in enumerate(model_sequence):
            stage = stages[i] if i < len(stages) else f"stage_{i + 1}"
            stage_instruction = {
                "draft": "Produce a first draft response to the following request.",
                "refine": "You are given a draft response. Improve it: fix any errors, improve clarity, and strengthen the argument.",
                "polish": "You are given a refined response. Polish it to production quality: perfect the tone, tighten the language, and ensure it is ready to use.",
            }.get(stage, f"Improve the following response (stage {stage}).")

            messages = [
                {"role": "system", "content": stage_instruction},
                {"role": "user", "content": current_content},
            ]
            response, latency = self._call(model, task_type, messages, progress_cb)
            stage_results.append({"stage": stage, "model": model, "response": response})
            timings[model] = latency
            current_content = f"Original request: {prompt}\n\nCurrent version:\n{response}"

        return {
            "final": stage_results[-1]["response"],
            "stages": stage_results,
            "timings": timings,
        }

    def run_debate(
        self,
        task_type: str,
        prompt: str,
        models: list[str],
        judge_model: str,
        progress_cb: Callable[[str], None] | None = None,
    ) -> dict:
        timings: dict[str, float] = {}

        # Round 1: independent answers
        round1: list[dict] = []
        for model in models:
            response, latency = self._call(
                model,
                task_type,
                [{"role": "user", "content": prompt}],
                progress_cb,
            )
            round1.append({"model": model, "response": response})
            timings[f"{model}_r1"] = latency

        # Round 2: critique and revise
        round2: list[dict] = []
        others_text = "\n\n".join(
            f"--- {r['model']} ---\n{r['response']}" for r in round1
        )
        for r in round1:
            critique_prompt = (
                f"Question: {prompt}\n\n"
                f"Your initial answer:\n{r['response']}\n\n"
                f"Other model responses:\n{others_text}\n\n"
                f"Review the other responses critically. Then produce your revised, improved final answer, "
                f"incorporating any valid points from others while defending your correct positions."
            )
            response, latency = self._call(
                r["model"],
                task_type,
                [{"role": "user", "content": critique_prompt}],
                progress_cb,
            )
            round2.append({"model": r["model"], "response": response})
            timings[f"{r['model']}_r2"] = latency

        # Judge selects or synthesises best final answer
        round2_text = "\n\n".join(f"--- {r['model']} (revised) ---\n{r['response']}" for r in round2)
        judge_prompt = (
            f"You are a neutral judge evaluating debate responses.\n"
            f"Question: {prompt}\n\n"
            f"Revised answers after debate:\n{round2_text}\n\n"
            f"Select the best answer or synthesise a superior combined answer. "
            f"Give your final verdict:"
        )
        if progress_cb:
            progress_cb(f"{judge_model} (judge)")
        judge_start = time.time()
        final = self.client.chat(judge_model, [{"role": "user", "content": judge_prompt}])
        judge_latency = time.time() - judge_start
        self.benchmark.log(task_type, judge_model, len(judge_prompt), len(final), judge_latency)
        timings[f"{judge_model}(judge)"] = judge_latency

        return {
            "final": final,
            "round1": round1,
            "round2": round2,
            "timings": timings,
        }
