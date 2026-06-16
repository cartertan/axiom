from src.agents.base_agent import BaseAgent

_TASK_DESCRIPTION = (
    "Your job is to analyse an RFP (Request for Proposal) excerpt for a PKI/security "
    "solutions architect preparing a response.\n"
    "Produce a structured analysis with exactly these sections, in this order:\n\n"
    "## Key Requirements\n"
    "[Numbered list of every distinct requirement stated or implied in the RFP text]\n\n"
    "## Compliance Items\n"
    "**Must-have:** [bullet list of mandatory requirements]\n"
    "**Nice-to-have:** [bullet list of optional/preferred requirements]\n\n"
    "## Potential Gaps or Risks\n"
    "[Bullet list of ambiguities, missing information, or areas of technical/commercial risk]\n\n"
    "## Recommended Response Strategy\n"
    "[Concrete, actionable guidance for how to position the response]\n\n"
    "Be precise and grounded only in what the RFP text states or clearly implies — do not invent requirements."
)


class RFPAgent(BaseAgent):
    def run(self, user_input: str, task_type: str = "RFP_ANALYSIS") -> str:
        """Analyse RFP text using qwen3:30b with thinking mode and return a
        structured analysis covering requirements, compliance, gaps, and strategy."""
        task_cfg = self.config["task_models"]["rfp_analysis"]
        model = task_cfg["primary"]
        thinking_mode = task_cfg.get("thinking_mode", False)

        past_context = self.memory.retrieve_context(user_input)
        system_prompt = self.build_system_prompt(_TASK_DESCRIPTION)
        if past_context:
            system_prompt += f"\n\n{past_context}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Analyse this RFP text:\n\n{user_input}"},
        ]

        response = self.ollama.chat(model, messages, think=thinking_mode)
        self.log_to_memory(task_type, user_input, response, model)
        return response
