import sys
import time

import yaml

from src.agents.email_agent import EmailAgent
from src.agents.general_agent import GeneralAgent
from src.agents.meeting_agent import MeetingAgent
from src.agents.pki_agent import PKIAgent
from src.agents.research_agent import ResearchAgent
from src.agents.rfp_agent import RFPAgent
from src.benchmark.logger import BenchmarkLogger
from src.core.memory import AxiomMemory
from src.core.ollama_client import OllamaClient, OllamaConnectionError
from src.core.profile import ProfileLoader
from src.core.router import TaskRouter
from src.interface.cli import AxiomCLI
from src.rag.retriever import PKIRetriever


def load_config(path: str = "config/models.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def get_agent(task_type: str, config, profile, memory, client, pki_retriever):
    if task_type == "EMAIL_DRAFT":
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


def run_benchmark(task_arg: str, config, profile, memory, client, benchmark, cli):
    from rich.table import Table

    task_type = task_arg.upper() if task_arg else "EMAIL_DRAFT"
    defaults = {
        "EMAIL_DRAFT": "Draft a follow-up email to a customer about a PKI renewal proposal.",
        "MEETING_SUMMARY": "Met with John and Sarah. Discussed PKI timeline. Certs by Q3. Proposal by Monday.",
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

    try:
        if not args:
            interactive_mode(config, profile, memory, client, router, benchmark, cli, pki_retriever)

        elif args[0] == "benchmark":
            task_arg = args[2] if len(args) >= 3 and args[1] == "--task" else "EMAIL_DRAFT"
            run_benchmark(task_arg, config, profile, memory, client, benchmark, cli)

        else:
            user_input = " ".join(args)
            cli.print_banner()
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
