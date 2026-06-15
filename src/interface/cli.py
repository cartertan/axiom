from rich.console import Console
from rich.panel import Panel
from rich.text import Text

_TASK_COLOURS = {
    "EMAIL_DRAFT": "blue",
    "MEETING_SUMMARY": "green",
    "PKI_QA": "yellow",
    "GENERAL": "white",
    "RESEARCH": "magenta",
    "RFP_ANALYSIS": "red",
    "BENCHMARK": "cyan",
}

_BANNER = (
    "  AXIOM\n"
    "  The reasoning behind every\n"
    "  decision."
)


class AxiomCLI:
    def __init__(self):
        self.console = Console()

    def print_banner(self) -> None:
        """Print the AXIOM banner panel."""
        self.console.print(Panel(_BANNER, border_style="bold white", expand=False))

    def print_response(
        self, response: str, task_type: str, model: str, latency: float
    ) -> None:
        """Print the agent response in a colour-coded panel with task/model/latency metadata."""
        colour = _TASK_COLOURS.get(task_type, "white")
        header = Text(f"{task_type}  ·  {model}", style="dim")
        footer = Text(f"⏱  {latency:.1f}s", style="dim")
        self.console.print(header)
        self.console.print(Panel(response, border_style=colour))
        self.console.print(footer)

    def print_error(self, message: str) -> None:
        """Print an error message in a red panel."""
        self.console.print(Panel(f"[bold red]Error:[/bold red] {message}", border_style="red"))

    def print_thinking(self) -> None:
        """Print a simple thinking indicator (non-blocking)."""
        self.console.print("[dim]Thinking...[/dim]")

    def get_input(self, prompt: str = "axiom> ") -> str:
        """Prompt the user for input with styled prompt text."""
        return self.console.input(f"[bold cyan]{prompt}[/bold cyan]")
