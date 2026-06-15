from src.agents.base_agent import BaseAgent

_TASK_DESCRIPTION = (
    "Your job is to draft a professional email on behalf of Carter Tan.\n"
    "Tone: direct, confident, customer-focused — not stiff, not casual.\n"
    "Format: start with 'Subject:' on its own line, then a blank line, then the email body.\n"
    "Keep it concise. End with a clear next step or call to action.\n"
    "No fluff. No filler. Sign off as Carter Tan."
)


class EmailAgent(BaseAgent):
    def run(self, user_input: str, task_type: str = "EMAIL_DRAFT") -> str:
        """Draft a professional email using qwen3.6:27b and return the formatted result."""
        model = self.config["task_models"]["email_draft"]["primary"]

        past_context = self.memory.retrieve_context(user_input)
        system_prompt = self.build_system_prompt(_TASK_DESCRIPTION)
        if past_context:
            system_prompt += f"\n\n{past_context}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ]

        response = self.ollama.chat(model, messages)
        self.log_to_memory(task_type, user_input, response, model)
        return response
