from src.agents.base_agent import BaseAgent
from src.core.memory import AxiomMemory
from src.core.ollama_client import OllamaClient
from src.core.profile import ProfileLoader
from src.rag.retriever import PKIRetriever

_TASK_DESCRIPTION = (
    "Your job is to answer a PKI (Public Key Infrastructure) question for a presales "
    "solutions architect, in language suitable for explaining directly to a customer "
    "at CIO/CISO level — clear, accurate, and free of unnecessary jargon.\n"
    "Use the retrieved PKI knowledge base context below if it is relevant. "
    "If you draw on a specific piece of context, cite its source file in parentheses, "
    "e.g. (source: ocsp.md).\n"
    "If no knowledge base context is provided or it doesn't cover the question, "
    "answer from your own knowledge and explicitly note that the answer is not "
    "sourced from the AXIOM knowledge base."
)

class PKIAgent(BaseAgent):
    def __init__(
        self,
        config: dict,
        profile_loader: ProfileLoader,
        memory: AxiomMemory,
        ollama_client: OllamaClient,
        retriever: PKIRetriever,
    ):
        super().__init__(config, profile_loader, memory, ollama_client)
        self.retriever = retriever

    def run(self, user_input: str, task_type: str = "PKI_QA") -> str:
        """Answer a PKI question using qwen3.6:27b, grounded in retrieved
        knowledge base context where available, with source citations."""
        model = self.config["task_models"]["pki_qa"]["primary"]

        kb_context = self.retriever.retrieve(user_input)
        has_context = bool(kb_context) and not kb_context.startswith(
            "[No PKI knowledge base indexed yet"
        )

        system_prompt = self.build_system_prompt(_TASK_DESCRIPTION)
        if has_context:
            system_prompt += f"\n\n{kb_context}"
        else:
            system_prompt += (
                "\n\n[No relevant knowledge base context found — answer from model "
                "knowledge and note this explicitly.]"
            )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ]

        response = self.ollama.chat(model, messages)
        self.log_to_memory(task_type, user_input, response, model)
        return response
