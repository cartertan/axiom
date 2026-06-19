import re
import subprocess

from src.actions.safety_gate import SafetyGate
from src.agents.email_agent import EmailAgent

_EXTRACT_RECIPIENT_PROMPT = (
    "Extract the recipient email address from the following user request. "
    "Return ONLY the email address, nothing else. "
    "If no email address is present, return the word 'unknown'."
)


class EmailSenderAgent(EmailAgent):
    def __init__(self, config, profile, memory, ollama_client):
        super().__init__(config, profile, memory, ollama_client)
        self._gate = SafetyGate()

    def _extract_recipient(self, user_input: str) -> str | None:
        # Fast regex pass first
        match = re.search(r"[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}", user_input)
        if match:
            return match.group(0)

        # Fall back to model extraction
        model = self.config["task_models"]["general"]["primary"]
        messages = [
            {"role": "system", "content": _EXTRACT_RECIPIENT_PROMPT},
            {"role": "user", "content": user_input},
        ]
        result = self.ollama.chat(model, messages).strip()
        if result.lower() == "unknown" or "@" not in result:
            return None
        return result

    def _extract_subject(self, draft: str) -> str:
        for line in draft.splitlines():
            if line.lower().startswith("subject:"):
                return line.split(":", 1)[1].strip()
        return "(no subject)"

    def _extract_body(self, draft: str) -> str:
        lines = draft.splitlines()
        # Skip the Subject: line and any blank lines immediately after
        in_body = False
        body_lines = []
        for line in lines:
            if not in_body:
                if line.lower().startswith("subject:"):
                    in_body = True
                    continue
            else:
                body_lines.append(line)
        body = "\n".join(body_lines).strip()
        return body if body else draft

    def _send_via_applescript(self, to: str, subject: str, body: str) -> None:
        escaped_body = body.replace('"', '\\"').replace("\n", "\\n")
        script = f"""
tell application "Mail"
    set newMessage to make new outgoing message with properties {{\\
        subject:"{subject}",\\
        content:"{escaped_body}",\\
        visible:true}}
    tell newMessage
        make new to recipient at end of to recipients with properties {{\\
            address:"{to}"}}
    end tell
    send newMessage
end tell
"""
        subprocess.run(["osascript", "-e", script], check=True)

    def run(self, user_input: str, task_type: str = "EMAIL_SEND") -> str:
        # Step 1: Draft using parent EmailAgent
        draft = super().run(user_input, "EMAIL_DRAFT")

        # Step 2: Extract recipient
        recipient = self._extract_recipient(user_input)
        if not recipient:
            return (
                f"Draft ready but I need a recipient address to send.\n\n{draft}\n\n"
                "Please re-run with the recipient email address in your request."
            )

        subject = self._extract_subject(draft)
        body_preview = self._extract_body(draft)[:300]

        # Step 3: Safety gate — must confirm before sending
        approved = self._gate.confirm_action(
            "Send email via macOS Mail",
            {
                "to": recipient,
                "subject": subject,
                "body_preview": body_preview + ("..." if len(body_preview) >= 300 else ""),
            },
        )

        if not approved:
            return f"Email NOT sent (declined at safety gate).\n\nDraft for reference:\n{draft}"

        # Step 4: Send
        try:
            self._send_via_applescript(recipient, subject, self._extract_body(draft))
        except subprocess.CalledProcessError as e:
            return f"Send failed (AppleScript error): {e}\n\nDraft:\n{draft}"

        self.log_to_memory(task_type, user_input, f"Email sent to {recipient}: {subject}", self.config["task_models"]["email_draft"]["primary"])
        return f"Email sent to {recipient}\nSubject: {subject}"
