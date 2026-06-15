import requests


class OllamaConnectionError(Exception):
    pass


class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip("/")

    def chat(self, model: str, messages: list, stream: bool = False) -> str:
        """Send a chat request to Ollama and return the response text."""
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={"model": model, "messages": messages, "stream": stream},
                timeout=300,
            )
            response.raise_for_status()
            return response.json()["message"]["content"]
        except requests.exceptions.ConnectionError:
            raise OllamaConnectionError(
                f"Cannot connect to Ollama at {self.base_url}. Is Ollama running? Try: ollama serve"
            )
        except requests.exceptions.RequestException as e:
            raise OllamaConnectionError(f"Ollama request failed: {e}")

    def embed(self, text: str) -> list:
        """Generate an embedding vector for the given text using nomic-embed-text."""
        try:
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json={"model": "nomic-embed-text", "prompt": text},
                timeout=60,
            )
            response.raise_for_status()
            return response.json()["embedding"]
        except requests.exceptions.ConnectionError:
            raise OllamaConnectionError(
                f"Cannot connect to Ollama at {self.base_url}. Is Ollama running? Try: ollama serve"
            )
        except requests.exceptions.RequestException as e:
            raise OllamaConnectionError(f"Ollama embed request failed: {e}")

    def list_models(self) -> list:
        """Return a list of available model name strings."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            response.raise_for_status()
            return [m["name"] for m in response.json().get("models", [])]
        except requests.exceptions.ConnectionError:
            raise OllamaConnectionError(
                f"Cannot connect to Ollama at {self.base_url}. Is Ollama running? Try: ollama serve"
            )
        except requests.exceptions.RequestException as e:
            raise OllamaConnectionError(f"Ollama list_models request failed: {e}")

    def is_model_available(self, model_name: str) -> bool:
        """Check whether the given model is available in Ollama."""
        return model_name in self.list_models()
