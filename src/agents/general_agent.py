from src.agents.base_agent import BaseAgent

_TASK_DESCRIPTION = (
    "You are a concise, direct AI assistant supporting a cybersecurity solutions architect.\n"
    "Answer questions clearly and practically — no padding, no repetition.\n"
    "Use bullet points for lists. Keep responses tight unless depth is explicitly requested."
)


class GeneralAgent(BaseAgent):
    def run(self, user_input: str, task_type: str = "GENERAL") -> str:
        """Answer general questions using gemma4:e4b and return the response."""
        model = self.config["task_models"]["general"]["primary"]

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
