from abc import ABC, abstractmethod

from src.core.memory import AxiomMemory
from src.core.ollama_client import OllamaClient
from src.core.personality import PersonalityLayer
from src.core.profile import ProfileLoader


class BaseAgent(ABC):
    def __init__(
        self,
        config: dict,
        profile_loader: ProfileLoader,
        memory: AxiomMemory,
        ollama_client: OllamaClient,
    ):
        self.config = config
        self.profile = profile_loader
        self.memory = memory
        self.ollama = ollama_client
        self.personality = PersonalityLayer()

    @abstractmethod
    def run(self, user_input: str, task_type: str) -> str:
        """Execute the agent and return the response string."""

    def build_system_prompt(self, task_description: str) -> str:
        """Prepend the AXIOM personality block and Carter's profile to any
        task-specific system prompt, in that order."""
        personality_text = self.personality.get_personality_prompt()
        profile_text = self.profile.format_for_prompt()
        return f"{personality_text}\n\n{profile_text}\n\n{task_description}"

    def log_to_memory(
        self, task_type: str, user_input: str, response: str, model_used: str
    ) -> None:
        """Summarise the interaction and persist it to ChromaDB memory."""
        summary = f"Task: {task_type}. Input: {user_input[:200]}. Response summary: {response[:300]}"
        self.memory.store_interaction(
            task_type=task_type,
            summary=summary,
            entities=[],
            model_used=model_used,
        )
