"""
AXIOM Council Orchestrator
Runs the four-agent deliberation pipeline and surfaces a final recommendation.
"""

from datetime import datetime

from src.agents.council.roles import (
    architect_agent,
    devils_advocate_agent,
    reviewer_agent,
    security_agent,
)
from src.integrations.obsidian import get_vault_context, write_note

ROLE_ORDER_FULL = ["Architect", "Security", "Devil's Advocate", "Reviewer"]
ROLE_ORDER_QUICK = ["Architect", "Reviewer"]


def run_council(question: str, quick: bool = False, save_vault: bool = False) -> dict:
    """
    Run the multi-agent council deliberation.

    Args:
        question:   The question or decision to deliberate on.
        quick:      If True, skip Security and Devil's Advocate — Architect → Reviewer only.
        save_vault: If True, write the final recommendation to the Obsidian vault.

    Returns:
        Dict with keys: question, quick, vault_context, responses (list), reviewer,
        timestamp, saved_to (path or None).
    """
    mode = "quick" if quick else "full"
    print(f"\n[COUNCIL] Starting {mode} deliberation")
    print(f"[COUNCIL] Question: {question}\n")

    # Step 1 — vault context
    vault_context = get_vault_context(question)
    if vault_context:
        print("[COUNCIL] Vault context loaded\n")

    responses = []

    # Step 2 — Architect (always runs)
    print(f"[COUNCIL] Running Architect (qwen3.6:27b)...")
    arch = architect_agent(question, vault_context=vault_context)
    responses.append(arch)
    _print_step_status(arch)

    if not quick:
        # Step 3 — Security
        print(f"[COUNCIL] Running Security (deepseek-r1:32b)...")
        sec = security_agent(
            question,
            architect_response=arch["content"],
            vault_context=vault_context,
        )
        responses.append(sec)
        _print_step_status(sec)

        # Step 4 — Devil's Advocate
        print(f"[COUNCIL] Running Devil's Advocate (qwen3:30b)...")
        da = devils_advocate_agent(
            question,
            architect_response=arch["content"],
            security_response=sec["content"],
            vault_context=vault_context,
        )
        responses.append(da)
        _print_step_status(da)

    # Step 5 — Reviewer (always runs, sees all prior responses)
    print(f"[COUNCIL] Running Reviewer (qwen3:30b)...")
    rev = reviewer_agent(question, all_responses=responses, vault_context=vault_context)
    responses.append(rev)
    _print_step_status(rev)

    timestamp = datetime.now().isoformat(timespec="seconds")
    saved_to = None

    # Step 6 — optional vault save
    if save_vault and not rev["error"]:
        title = f"Council — {question[:60]}"
        body = _format_vault_body(question, responses, mode)
        saved_to = write_note(
            folder="decisions",
            title=title,
            content=body,
            tags=["council", "decision"],
            provenance="decision",
            model="council",
        )

    print(f"\n[COUNCIL] Deliberation complete ({timestamp})\n")

    return {
        "question": question,
        "quick": quick,
        "vault_context": vault_context,
        "responses": responses,
        "reviewer": rev,
        "timestamp": timestamp,
        "saved_to": saved_to,
    }


def print_council_output(result: dict) -> None:
    """Print a clean, readable council deliberation to the terminal."""
    sep = "=" * 72
    thin = "-" * 72

    print(f"\n{sep}")
    print(f"  AXIOM COUNCIL DELIBERATION")
    print(f"  {result['timestamp']}")
    print(sep)
    print(f"\n  Q: {result['question']}\n")

    for resp in result["responses"]:
        role = resp["role"]
        model = resp["model"]
        content = resp["content"]

        print(thin)
        print(f"  [{role.upper()}]  ({model})")
        print(thin)

        if resp["error"]:
            print(f"  ERROR: {content}\n")
        else:
            # Indent each line for readability
            for line in content.splitlines():
                print(f"  {line}")
            print()

    print(sep)
    if result.get("saved_to"):
        print(f"  Saved to vault: {result['saved_to']}")
        print(sep)
    print()


# ── internal helpers ──────────────────────────────────────────────────────────

def _print_step_status(resp: dict) -> None:
    status = "ERROR" if resp["error"] else "done"
    print(f"  [{resp['role']}] {status}\n")


def _format_vault_body(question: str, responses: list, mode: str) -> str:
    lines = [f"**Question:** {question}\n", f"**Mode:** {mode}\n"]
    for resp in responses:
        lines.append(f"\n## {resp['role']} ({resp['model']})\n")
        lines.append(resp["content"] if not resp["error"] else f"_Error: {resp['content']}_")
        lines.append("")
    return "\n".join(lines)
