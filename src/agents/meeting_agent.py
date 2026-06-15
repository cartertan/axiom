from src.agents.base_agent import BaseAgent

_TASK_DESCRIPTION = (
    "Your job is to summarise meeting notes into a structured format.\n"
    "You MUST output all six sections below, in this exact order:\n\n"
    "## Meeting Summary\n"
    "**Date:** [extract from notes, or 'Not specified']\n"
    "**Attendees:** [list all mentioned names and organisations]\n"
    "**Key Decisions:** [bullet list of decisions made]\n"
    "**Action Items:** [bullet list — include owner if mentioned]\n"
    "**Next Steps:** [bullet list of follow-up actions]\n"
    "**Follow-up Date:** [extract if mentioned, or 'TBD']\n\n"
    "Be concise. Extract only what is in the notes — do not invent information."
)


class MeetingAgent(BaseAgent):
    def run(self, user_input: str, task_type: str = "MEETING_SUMMARY") -> str:
        """Summarise meeting notes using granite4.1:30b and return structured output."""
        model = self.config["task_models"]["meeting_summary"]["primary"]

        system_prompt = self.build_system_prompt(_TASK_DESCRIPTION)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Summarise these meeting notes:\n\n{user_input}"},
        ]

        response = self.ollama.chat(model, messages)
        self.log_to_memory(task_type, user_input, response, model)
        return response
