from src.core.ollama_client import OllamaClient

VALID_TASK_TYPES = {
    "EMAIL_DRAFT",
    "MEETING_SUMMARY",
    "RFP_ANALYSIS",
    "PKI_QA",
    "RESEARCH",
    "GENERAL",
    "BENCHMARK",
}

_SYSTEM_PROMPT = (
    "You are a task classifier. Respond with ONLY one of these exact strings — "
    "no explanation, no punctuation, no extra text:\n"
    "EMAIL_DRAFT, MEETING_SUMMARY, RFP_ANALYSIS, PKI_QA, RESEARCH, GENERAL, BENCHMARK"
)


class TaskRouter:
    def __init__(self, config: dict):
        self._config = config
        self._ollama = OllamaClient(
            base_url=config.get("ollama_base_url", "http://localhost:11434")
        )
        self._router_model = config.get("task_models", {}).get("router", {}).get(
            "primary", "gemma4:e4b"
        )

    def classify(self, user_input: str) -> str:
        """Classify user input into a task type string using the router model."""
        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": f"Classify this task: {user_input}"},
        ]
        raw = self._ollama.chat(self._router_model, messages).strip().upper()
        # Strip any accidental punctuation or extra words
        for task_type in VALID_TASK_TYPES:
            if task_type in raw:
                return task_type
        return "GENERAL"

    def get_model_for_task(self, task_type: str) -> tuple:
        """Return (primary_model, fallback_model, thinking_mode) for the given task type."""
        key = task_type.lower()
        task_cfg = self._config.get("task_models", {}).get(key, {})
        primary = task_cfg.get("primary", "gemma4:e4b")
        fallback = task_cfg.get("fallback", "gemma4:e4b")
        thinking_mode = task_cfg.get("thinking_mode", False)
        return primary, fallback, thinking_mode
