"""
AXIOM Council — Four Role Agents
Each role wraps an Ollama call with a fixed system prompt and persona.
Returns structured dict with role, model, content, where_run, error.
"""

import requests

OLLAMA_URL = "http://localhost:11434/api/generate"


def _call_ollama(model: str, system: str, prompt: str, timeout: int = 300) -> str:
    """Base Ollama call. Returns content string or error message."""
    payload = {
        "model": model,
        "system": system,
        "prompt": prompt,
        "stream": False,
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except requests.exceptions.Timeout:
        return f"ERROR: {model} timed out after {timeout}s"
    except Exception as e:
        return f"ERROR: {model} failed — {str(e)}"


def _parse_response(role: str, model: str, raw: str) -> dict:
    """Wrap raw model output into standard council response format."""
    return {
        "role": role,
        "model": model,
        "content": raw,
        "where_run": "local",
        "error": raw.startswith("ERROR:"),
    }


def architect_agent(question: str, vault_context: str = "") -> dict:
    """Architect role — qwen3.6:27b. Proposes solution design and implementation path."""
    system = """You are the Architect on AXIOM's multi-agent council.
Your role: propose a clear solution design with concrete implementation steps.
Focus on: architecture options, trade-offs, dependencies, and a recommended path.
Be specific and practical. Avoid vague generalities.
Structure your response as:
1. Recommended Approach
2. Architecture Rationale
3. Key Trade-offs
4. Implementation Steps
5. Dependencies / Risks"""

    prompt = f"{vault_context}\n\nQuestion: {question}" if vault_context else f"Question: {question}"
    raw = _call_ollama("qwen3.6:27b", system, prompt)
    return _parse_response("Architect", "qwen3.6:27b", raw)


def security_agent(question: str, architect_response: str = "", vault_context: str = "") -> dict:
    """Security role — deepseek-r1:32b. Identifies threat vectors and hardening requirements."""
    system = """You are the Security Specialist on AXIOM's multi-agent council.
Your role: identify security risks, threat vectors, and hardening requirements.
Focus on: attack surface, trust boundaries, cryptographic concerns, PKI implications,
zero-trust principles, audit requirements, and compliance considerations.
Challenge any assumptions in the Architect's proposal that create security risk.
Structure your response as:
1. Security Assessment
2. Key Risks / Threat Vectors
3. Hardening Recommendations
4. PKI / Cryptographic Considerations (if relevant)
5. Compliance / Audit Requirements"""

    context_parts = []
    if vault_context:
        context_parts.append(vault_context)
    if architect_response:
        context_parts.append(f"[Architect's Proposal]\n{architect_response}")
    context_parts.append(f"Question: {question}")
    prompt = "\n\n".join(context_parts)

    raw = _call_ollama("deepseek-r1:32b", system, prompt)
    return _parse_response("Security", "deepseek-r1:32b", raw)


def devils_advocate_agent(
    question: str,
    architect_response: str = "",
    security_response: str = "",
    vault_context: str = "",
) -> dict:
    """Devil's Advocate role — qwen3:30b. Challenges assumptions and stress-tests proposals."""
    system = """You are the Devil's Advocate on AXIOM's multi-agent council.
Your role: challenge assumptions, expose blind spots, and stress-test the proposed approach.
You are NOT here to obstruct — you are here to make the final decision stronger.
Focus on: what could go wrong, hidden assumptions, unconsidered alternatives,
scalability limits, edge cases, and second-order effects.
Be direct and specific. Vague concerns are worthless.
Structure your response as:
1. Critical Challenges
2. Flawed Assumptions
3. Unconsidered Alternatives
4. Worst-Case Scenarios
5. What Would Have to Be True for This to Fail"""

    context_parts = []
    if vault_context:
        context_parts.append(vault_context)
    if architect_response:
        context_parts.append(f"[Architect's Proposal]\n{architect_response}")
    if security_response:
        context_parts.append(f"[Security Assessment]\n{security_response}")
    context_parts.append(f"Question: {question}")
    prompt = "\n\n".join(context_parts)

    raw = _call_ollama("qwen3:30b", system, prompt)
    return _parse_response("Devil's Advocate", "qwen3:30b", raw)


def reviewer_agent(question: str, all_responses: list = None, vault_context: str = "") -> dict:
    """Reviewer role — qwen3:30b. Synthesises council deliberation into a final recommendation."""
    system = """You are the Reviewer on AXIOM's multi-agent council.
Your role: synthesise the full deliberation and produce a final, actionable recommendation.
You have read every council member's input. Now cut through the noise.
Focus on: what the council agrees on, where disagreements are real vs. superficial,
what the single best path forward is, and what must be done first.
Be decisive. Hedging is not useful here.
Structure your response as:
1. Council Consensus
2. Key Points of Disagreement
3. Final Recommendation
4. Immediate Next Steps (ordered)
5. Open Questions That Remain"""

    context_parts = []
    if vault_context:
        context_parts.append(vault_context)
    for resp in (all_responses or []):
        if not resp.get("error") and resp.get("content"):
            context_parts.append(f"[{resp['role']} — {resp['model']}]\n{resp['content']}")
    context_parts.append(f"Original Question: {question}")
    prompt = "\n\n".join(context_parts)

    raw = _call_ollama("qwen3:30b", system, prompt)
    return _parse_response("Reviewer", "qwen3:30b", raw)
