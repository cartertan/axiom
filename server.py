import sys

import uvicorn

from src.core.ollama_client import OllamaClient, OllamaConnectionError
from src.interface.cli import AxiomCLI

_HOST = "127.0.0.1"
_PORT = 8000


def main():
    cli = AxiomCLI()
    cli.print_banner()

    try:
        OllamaClient().list_models()
    except OllamaConnectionError as e:
        cli.print_error(f"{e}\nIs Ollama running? Try: ollama serve")
        sys.exit(1)

    cli.console.print(f"[bold]AXIOM web interface starting at http://{_HOST}:{_PORT}[/bold]\n")
    uvicorn.run("src.interface.web.app:app", host=_HOST, port=_PORT)


if __name__ == "__main__":
    main()
