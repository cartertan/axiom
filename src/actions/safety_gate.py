from datetime import datetime, timezone


class SafetyGate:
    def confirm_action(self, description: str, details: dict) -> bool:
        """Print what AXIOM is about to do and prompt for explicit confirmation.
        Returns True only on 'yes', 'y', or 'confirm'. Logs every decision."""
        print("\n" + "=" * 60)
        print(f"AXIOM ACTION: {description}")
        for key, value in details.items():
            print(f"  {key}: {value}")
        print("=" * 60)

        try:
            answer = input("Confirm? (yes/no): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            answer = "no"

        approved = answer in ("yes", "y", "confirm")
        self._log(description, details, approved)
        return approved

    def _log(self, description: str, details: dict, approved: bool) -> None:
        ts = datetime.now(timezone.utc).isoformat()
        status = "APPROVED" if approved else "DECLINED"
        detail_str = ", ".join(f"{k}={v}" for k, v in details.items())
        print(f"[{ts}] SafetyGate {status}: {description} | {detail_str}")
