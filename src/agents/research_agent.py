from src.agents.base_agent import BaseAgent

_TASK_DESCRIPTION = (
    "Your job is to provide structured analytical research on the given topic for a "
    "PKI/security solutions architect. This is model-knowledge research only — "
    "no live web access is available, so note where information may be dated.\n"
    "Produce exactly these sections, in this order:\n\n"
    "## Overview\n"
    "[Concise framing of the topic and why it matters]\n\n"
    "## Key Players / Technologies / Considerations\n"
    "[Bullet list covering the relevant landscape]\n\n"
    "## Strategic Implications\n"
    "[What this means specifically for a PKI/security solutions architect]\n\n"
    "## Recommended Next Steps\n"
    "[Concrete, actionable next steps]\n\n"
    "Be analytical and specific — avoid generic statements that could apply to any topic."
)


class ResearchAgent(BaseAgent):
    def run(self, user_input: str, task_type: str = "RESEARCH") -> str:
        """Provide structured analytical research using deepseek-r1:32b and
        return the response covering overview, landscape, implications, and next steps."""
        task_cfg = self.config["task_models"]["research"]
        model = task_cfg["primary"]
        thinking_mode = task_cfg.get("thinking_mode", False)

        past_context = self.memory.retrieve_context(user_input)
        system_prompt = self.build_system_prompt(_TASK_DESCRIPTION)
        if past_context:
            system_prompt += f"\n\n{past_context}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Research this topic:\n\n{user_input}"},
        ]

        response = self.ollama.chat(model, messages, think=thinking_mode)
        self.log_to_memory(task_type, user_input, response, model)
        return response
