import sys
import time

import yaml

from src.agents.email_agent import EmailAgent
from src.agents.email_sender_agent import EmailSenderAgent
from src.agents.general_agent import GeneralAgent
from src.agents.meeting_agent import MeetingAgent
from src.agents.pki_agent import PKIAgent
from src.agents.research_agent import ResearchAgent
from src.agents.rfp_agent import RFPAgent
from src.benchmark.logger import BenchmarkLogger
from src.core.memory import AxiomMemory
from src.core.ollama_client import OllamaClient, OllamaConnectionError
from src.core.orchestrator import Orchestrator
from src.core.profile import ProfileLoader
from src.core.router import TaskRouter
from src.interface.cli import AxiomCLI
from src.rag.retriever import PKIRetriever


def load_config(path: str = "config/models.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def get_agent(task_type: str, config, profile, memory, client, pki_retriever):
    if task_type in ("EMAIL_DRAFT", "EMAIL_SEND"):
        if task_type == "EMAIL_SEND":
            return EmailSenderAgent(config, profile, memory, client)
        return EmailAgent(config, profile, memory, client)
    if task_type == "MEETING_SUMMARY":
        return MeetingAgent(config, profile, memory, client)
    if task_type == "RFP_ANALYSIS":
        return RFPAgent(config, profile, memory, client)
    if task_type == "PKI_QA":
        return PKIAgent(config, profile, memory, client, pki_retriever)
    if task_type == "RESEARCH":
        return ResearchAgent(config, profile, memory, client)
    return GeneralAgent(config, profile, memory, client)


def run_single_task(
    user_input: str, config, profile, memory, client, router, benchmark, cli, pki_retriever
):
    cli.print_thinking()
    task_type = router.classify(user_input)
    agent = get_agent(task_type, config, profile, memory, client, pki_retriever)
    model, _, _ = router.get_model_for_task(task_type)

    start = time.time()
    response = agent.run(user_input, task_type)
    latency = time.time() - start

    benchmark.log(task_type, model, len(user_input), len(response), latency)
    cli.print_response(response, task_type, model, latency)


def run_orchestrated_task(
    user_input: str,
    mode: str,
    config,
    profile,
    memory,
    client,
    router,
    benchmark,
    cli,
    pki_retriever,
):
    orch_cfg = config.get("orchestration", {})
    task_type = router.classify(user_input)

    def progress_cb(model_name: str):
        cli.console.print(f"[dim]  Running {model_name}...[/dim]")

    orchestrator = Orchestrator(client, benchmark)

    cli.console.print(f"\n[bold cyan]AXIOM[/bold cyan] [dim]Orchestration mode: {mode}[/dim]")

    if mode == "ensemble":
        models = orch_cfg.get("ensemble", {}).get("default_models", [])
        synthesiser = orch_cfg.get("ensemble", {}).get("synthesiser", models[0])
        result = orchestrator.run_ensemble(task_type, user_input, models, synthesiser, progress_cb)
    elif mode == "pipeline":
        sequence = orch_cfg.get("pipeline", {}).get("default_sequence", [])
        result = orchestrator.run_pipeline(task_type, user_input, sequence, progress_cb)
    elif mode == "debate":
        models = orch_cfg.get("debate", {}).get("default_models", [])
        judge = orch_cfg.get("debate", {}).get("judge", models[0])
        result = orchestrator.run_debate(task_type, user_input, models, judge, progress_cb)
    else:
        raise ValueError(f"Unknown orchestration mode: {mode}")

    total_latency = sum(result["timings"].values())
    cli.print_response(result["final"], task_type, f"[{mode}]", round(total_latency, 1))

    # Show per-model breakdown on request
    if mode == "ensemble":
        cli.console.print("\n[dim]Individual responses:[/dim]")
        for r in result["individual_responses"]:
            cli.console.print(f"[dim]  [{r['model']}] {r['response'][:120]}...[/dim]")
    elif mode == "pipeline":
        cli.console.print("\n[dim]Pipeline stages:[/dim]")
        for s in result["stages"]:
            cli.console.print(f"[dim]  [{s['stage']} / {s['model']}] {s['response'][:120]}...[/dim]")
    elif mode == "debate":
        cli.console.print("\n[dim]Debate round 1:[/dim]")
        for r in result["round1"]:
            cli.console.print(f"[dim]  [{r['model']}] {r['response'][:120]}...[/dim]")


def run_benchmark(task_arg: str, config, profile, memory, client, benchmark, cli):
    from rich.table import Table

    task_type = task_arg.upper() if task_arg else "EMAIL_DRAFT"
    defaults = {
        "EMAIL_DRAFT": "Draft a follow-up email to a customer about a PKI renewal proposal.",
        "MEETING_SUMMARY": "Met with John and Sarah. Discussed PKI timeline. Certs by Q3. Proposal by Monday.",
        "PKI_QA": "What is OCSP stapling and how do I explain it to a CIO?",
        "GENERAL": "What is OCSP stapling and how do I explain it to a CIO?",
    }
    test_prompt = defaults.get(task_type, defaults["GENERAL"])

    cli.console.print(f"\n[bold]Benchmark:[/bold] {task_type}\n[dim]Prompt:[/dim] {test_prompt}\n")

    benchmark_models = config.get("benchmark_models", [])
    results = []

    for model in benchmark_models:
        cli.console.print(f"[dim]Running {model}...[/dim]")
        try:
            start = time.time()
            response = client.chat(
                model,
                [{"role": "user", "content": test_prompt}],
            )
            latency = time.time() - start
            tps = round(len(response) / latency, 1) if latency > 0 else 0
            benchmark.log(task_type, model, len(test_prompt), len(response), latency)
            results.append((model, round(latency, 1), tps, "OK"))
        except Exception as e:
            results.append((model, "-", "-", f"ERROR: {e}"))

    table = Table(title=f"Benchmark Results — {task_type}", show_lines=True)
    table.add_column("Model", style="cyan")
    table.add_column("Latency (s)", justify="right")
    table.add_column("Chars/s", justify="right")
    table.add_column("Status")

    for model, latency, tps, status in results:
        table.add_row(model, str(latency), str(tps), status)

    cli.console.print(table)


def interactive_mode(config, profile, memory, client, router, benchmark, cli, pki_retriever):
    cli.print_banner()
    cli.console.print("[dim]Type your task, or 'quit' to exit.[/dim]\n")
    while True:
        try:
            user_input = cli.get_input()
            if user_input.strip().lower() in ("quit", "exit", "q"):
                cli.console.print("[dim]Goodbye.[/dim]")
                break
            if not user_input.strip():
                continue
            run_single_task(
                user_input, config, profile, memory, client, router, benchmark, cli, pki_retriever
            )
        except KeyboardInterrupt:
            cli.console.print("\n[dim]Goodbye.[/dim]")
            break


def _parse_mode(args: list[str]) -> tuple[str | None, list[str]]:
    """Extract --mode VALUE from args, return (mode_or_None, remaining_args)."""
    if "--mode" in args:
        idx = args.index("--mode")
        if idx + 1 < len(args):
            mode = args[idx + 1]
            remaining = args[:idx] + args[idx + 2:]
            return mode, remaining
    return None, args


def main():
    cli = AxiomCLI()

    try:
        config = load_config()
        client = OllamaClient(base_url=config.get("ollama_base_url", "http://localhost:11434"))
        profile = ProfileLoader()
        memory = AxiomMemory()
        router = TaskRouter(config)
        benchmark = BenchmarkLogger()
        pki_retriever = PKIRetriever()
    except OllamaConnectionError as e:
        cli.print_error(f"{e}\nIs Ollama running? Try: ollama serve")
        sys.exit(1)
    except Exception as e:
        cli.print_error(f"Startup failed: {e}")
        sys.exit(1)

    args = sys.argv[1:]
    mode, args = _parse_mode(args)

    try:
        if not args:
            if mode:
                cli.print_error("No prompt given. Usage: axiom.py <prompt> --mode <mode>")
                sys.exit(1)
            interactive_mode(config, profile, memory, client, router, benchmark, cli, pki_retriever)

        elif args[0] == "benchmark":
            task_arg = args[2] if len(args) >= 3 and args[1] == "--task" else "EMAIL_DRAFT"
            if len(args) >= 3 and args[1] == "--task":
                # Interactive quality-rated benchmark via BenchmarkRunner
                from src.benchmark.runner import BenchmarkRunner
                defaults = {
                    "EMAIL_DRAFT": "Draft a follow-up email to a customer about a PKI renewal proposal.",
                    "MEETING_SUMMARY": "Met with John and Sarah. Discussed PKI timeline. Certs by Q3. Proposal by Monday.",
                    "PKI_QA": "What is OCSP stapling and how do I explain it to a CIO?",
                    "GENERAL": "What is OCSP stapling and how do I explain it to a CIO?",
                }
                task_type = task_arg.upper()
                prompt = defaults.get(task_type, defaults["GENERAL"])
                models = config.get("benchmark_models", [])
                runner = BenchmarkRunner(client, benchmark)
                runner.run_benchmark(task_type, prompt, models)
            else:
                run_benchmark(task_arg, config, profile, memory, client, benchmark, cli)

        elif args[0] == "task":
            from src.agents.task_agent import TaskAgent
            ta = TaskAgent(config, profile, memory, client)
            sub_args = args[1:]
            user_input = " ".join(sub_args)
            result = ta.run(user_input, "TASK_MANAGEMENT")
            cli.console.print(f"\n{result}\n")

        elif args[0] == "research":
            from src.agents.research_web_agent import ResearchWebAgent
            query = " ".join(args[1:])
            cli.print_banner()
            agent = ResearchWebAgent(config, profile, memory, client)
            cli.print_thinking()
            result = agent.run(query, "RESEARCH")
            cli.print_response(result, "RESEARCH", config["task_models"]["research"]["primary"], 0)

        else:
            user_input = " ".join(args)
            cli.print_banner()

            # Determine effective mode
            effective_mode = mode
            if not effective_mode:
                task_type = router.classify(user_input)
                multi_model_tasks = config.get("orchestration", {}).get("multi_model_tasks", [])
                if task_type in multi_model_tasks:
                    effective_mode = "ensemble"

            if effective_mode and effective_mode != "single":
                run_orchestrated_task(
                    user_input, effective_mode, config, profile, memory, client,
                    router, benchmark, cli, pki_retriever,
                )
            else:
                run_single_task(
                    user_input, config, profile, memory, client, router, benchmark, cli, pki_retriever
                )

    except OllamaConnectionError as e:
        cli.print_error(f"{e}\nIs Ollama running? Try: ollama serve")
        sys.exit(1)
    except Exception as e:
        cli.print_error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
