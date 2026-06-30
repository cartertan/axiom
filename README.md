# AXIOM — The Reasoning Behind Every Decision

> Personal AI assistant agent running fully local on Apple Silicon via Ollama.
> Multi-agent council · Voice interface · Obsidian brain · GLM-5.2 cloud escalation

---

## What AXIOM Does

- Answers questions using multiple specialist AI models simultaneously
- Runs a 4-role council (Architect · Security · Devil's Advocate · Reviewer)
- Speaks and listens via voice interface (whisper.cpp STT + Voxtral TTS)
- Remembers decisions in an Obsidian vault (reads context, writes decisions back)
- Routes complex questions to GLM-5.2 via OpenRouter automatically
- Drafts emails, summarises meetings, analyses RFPs, answers PKI questions
- Runs a DuckDuckGo-powered web research agent

---

## Phase Roadmap

| Version | What it added | Status |
|---------|---------------|--------|
| v0.1.0 | CLI + ChromaDB memory + email/meeting agents | ✅ Done |
| v0.2.0 | Personality layer + RFP/PKI/research agents + FastAPI web UI + RAG | ✅ Done |
| v0.3.0 | Ensemble/pipeline/debate modes + action layer + benchmark dashboard | ✅ Done |
| v0.4.0 | Voice: whisper.cpp STT (Metal GPU) + Voxtral TTS + push-to-talk | ✅ Done |
| v0.5.0 | Multi-agent council + Obsidian brain + GLM-5.2 via OpenRouter + voice UI | ✅ Done |

---

## Model Stack

| Model | Role |
|-------|------|
| qwen3:30b | Reasoning, council reviewer, devil's advocate |
| qwen3.6:27b | Writing, email, PKI Q&A, council architect |
| granite4.1:30b | Structured output, compliance, meetings |
| deepseek-r1:32b | Research, security reasoning, council security role |
| gemma4:e4b | Task routing, tool calling, vision |
| devstral-small-2 | Agentic coding |
| nomic-embed-text | RAG embeddings |

---

## Tech Stack

Python · FastAPI · ChromaDB · Ollama · whisper.cpp · mlx-audio/Voxtral ·
OpenRouter (GLM-5.2) · Obsidian vault · DuckDuckGo search · SQLite

---

## Quick Start

```bash
git clone https://github.com/cartertan/axiom
cd axiom
pip install -r requirements.txt
cp .env.example .env
# Add OPENROUTER_API_KEY to .env
python3 server.py
# Open http://localhost:8000
```

---

## Council Mode

AXIOM's council runs four specialist models sequentially:

1. **Architect** (qwen3.6:27b) — proposes solution design and implementation path
2. **Security** (deepseek-r1:32b) — identifies threat vectors and hardening requirements
3. **Devil's Advocate** (qwen3:30b) — challenges assumptions and stress-tests the proposal
4. **Reviewer** (GLM-5.2 / qwen3:30b fallback) — synthesises all inputs into a final recommendation

Council output is saved to the Obsidian vault under `decisions/` with a timestamp and all role responses.
