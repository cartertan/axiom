# AXIOM
**The reasoning behind every decision.**

AXIOM is a locally-run personal AI assistant built for Carter Tan — a Solutions Architect specialising in PKI and AI security. It runs entirely on-device via Ollama, with no cloud calls and no data leaving your machine. AXIOM classifies your intent, routes it to the right model, drafts emails in your voice, summarises meeting notes in structured format, analyses RFPs, answers PKI questions grounded in a local knowledge base, and runs research tasks — from the terminal or a browser. Memory persists across sessions via ChromaDB.

---

## The Five-Layer Vision

AXIOM is being built up toward a JARVIS-style assistant, one layer at a time:

1. **Brain** — local LLM routing and reasoning, no cloud dependency (Phase 1)
2. **Personality & Memory** — a consistent identity across every agent, with persistent episodic memory (Phase 2)
3. **Domain Expertise** — specialised agents (RFP, PKI Q&A, Research) backed by a retrieval-augmented knowledge base (Phase 2)
4. **Interface** — reachable from a terminal or a browser, with file upload, not just a CLI (Phase 2)
5. **Autonomy** — proactive web research, calendar/email awareness, and scheduled tasks (Phase 3+)

---

## Phase 1 Capabilities

- **Email drafting** — professional emails in Carter's voice (qwen3.6:27b)
- **Meeting summaries** — structured 6-section output from raw notes (granite4.1:30b)
- **General Q&A** — fast answers for cybersecurity and architecture questions (gemma4:e4b)
- **Intent routing** — automatic task classification, no manual flags needed (gemma4:e4b)
- **Persistent memory** — ChromaDB episodic memory across sessions (nomic-embed-text)
- **Benchmark mode** — compare all models on any task, logs to CSV
- **Rich terminal UI** — colour-coded output panels, task/model/latency metadata

## Phase 2 Capabilities

- **AXIOM personality layer** — a consistent identity (calm, direct, never sycophantic) injected into every agent's system prompt
- **RFP analysis agent** — extracts requirements, compliance items, gaps, and response strategy (qwen3:30b, thinking mode)
- **PKI Q&A agent** — answers PKI/certificate questions grounded in a local knowledge base, with source citations (qwen3.6:27b + RAG)
- **Research agent** — structured analytical research on markets, vendors, and technologies (deepseek-r1:32b)
- **Web interface** — full chat UI in the browser, with PDF upload and colour-coded response badges
- **PKI knowledge base** — Markdown knowledge files indexed into ChromaDB and retrieved via semantic search

---

## Requirements

- Python 3.11+
- [Ollama](https://ollama.com) running locally (`ollama serve`)
- Models pulled:

| Model | Purpose |
|---|---|
| `qwen3.6:27b` | Email drafting, PKI Q&A |
| `granite4.1:30b` | Meeting summaries |
| `gemma4:e4b` | General Q&A, intent routing |
| `deepseek-r1:32b` | Research tasks |
| `qwen3:30b` | RFP analysis fallback |
| `nomic-embed-text` | ChromaDB embeddings |

Pull all models:
```bash
ollama pull qwen3.6:27b && ollama pull granite4.1:30b && ollama pull gemma4:e4b
ollama pull deepseek-r1:32b && ollama pull qwen3:30b && ollama pull nomic-embed-text
```

---

## Installation

```bash
git clone https://github.com/cartertan/axiom.git
cd axiom
pip install -r requirements.txt
cp .env.example .env
```

---

## Usage

### Single-task mode
```bash
python3 axiom.py "draft a follow-up email to the Singtel security team"
python3 axiom.py "summarise these meeting notes: [paste notes here]"
python3 axiom.py "what is OCSP stapling and how do I explain it to a CIO?"
```

### Benchmark mode
```bash
python3 axiom.py benchmark --task email_draft
python3 axiom.py benchmark --task meeting_summary
python3 axiom.py benchmark --task general
```

### Interactive mode
```bash
python3 axiom.py
```
Type your task at the `axiom>` prompt. Type `quit` to exit.

### Web interface
```bash
python3 server.py
```
Open `http://localhost:8000` in a browser. Local only — binds to `127.0.0.1`, never `0.0.0.0`.

- Chat with AXIOM the same way as the CLI; responses show a badge with task type, model, and latency
- Upload a PDF (📎) to extract its text straight into the message box
- All processing stays local — the web server calls the same Ollama instance as the CLI

![AXIOM web interface](docs/screenshots/web-ui.png)

---

## PKI Knowledge Base

`knowledge/pki/` holds Markdown reference files (OCSP, CRLs, certificate lifecycle, HSMs, post-quantum crypto) written for a presales solutions architect. They're chunked, embedded with `nomic-embed-text`, and stored in a dedicated ChromaDB collection (`axiom_pki_knowledge`) separate from episodic memory.

The `PKIAgent` retrieves relevant chunks for every PKI question and cites the source file inline. To rebuild the index after editing or adding knowledge files:

```bash
python3 -c "
from src.rag.indexer import PKIIndexer
PKIIndexer().rebuild()
"
```

---

## Project Structure

```
axiom/
├── axiom.py                    # CLI entry point
├── server.py                   # Web entry point
├── config/
│   ├── models.yaml              # Model assignments per task
│   └── personality.yaml         # AXIOM identity, character, rules
├── memory/carter_profile.json  # Carter DNA — injected into every prompt
├── knowledge/pki/              # PKI reference Markdown, indexed for RAG
├── src/
│   ├── core/
│   │   ├── ollama_client.py    # All Ollama API calls
│   │   ├── profile.py          # Profile loader
│   │   ├── personality.py      # AXIOM personality layer
│   │   ├── memory.py           # ChromaDB read/write
│   │   └── router.py           # Intent classification
│   ├── agents/
│   │   ├── base_agent.py       # Abstract base class
│   │   ├── email_agent.py      # Email drafting
│   │   ├── meeting_agent.py    # Meeting summaries
│   │   ├── general_agent.py    # General Q&A
│   │   ├── rfp_agent.py        # RFP analysis
│   │   ├── pki_agent.py        # PKI Q&A (RAG)
│   │   └── research_agent.py   # Structured research
│   ├── rag/
│   │   ├── indexer.py          # PKI knowledge base indexer
│   │   └── retriever.py        # PKI semantic retrieval
│   ├── benchmark/
│   │   └── logger.py           # CSV benchmark logger
│   └── interface/
│       ├── cli.py              # Rich terminal UI
│       └── web/                # FastAPI app, templates, static assets
└── data/benchmarks/            # benchmark_results.csv (gitignored)
```

---

## Model Stack

| Task | Primary | Fallback |
|---|---|---|
| Email draft | qwen3.6:27b | granite4.1:30b |
| Meeting summary | granite4.1:30b | qwen3.6:27b |
| PKI Q&A | qwen3.6:27b | granite4.1:30b |
| Research | deepseek-r1:32b | qwen3:30b |
| RFP analysis | qwen3:30b | deepseek-r1:32b |
| General | gemma4:e4b | granite4.1:30b |
| Router | gemma4:e4b | — |

---

## Roadmap

| Phase | Focus | Status |
|---|---|---|
| **v0.1.0** | CLI assistant — routing, email, meetings, general Q&A, memory, benchmarks | ✅ Done |
| **v0.2.0** | Personality layer, RFP/PKI/Research agents, PKI knowledge base + RAG, web UI | ✅ Done |
| **v0.3.0** | Automatic model selection via benchmark feedback loop | Planned |
| **v0.4.0** | Web search agent + broader document ingestion (tenders, security specs) | Planned |
| **v0.5.0** | Calendar/email awareness, scheduled tasks, Strava integration | Planned |

---

## Author

**Carter Tan** — Solutions Architect, AI Security Specialist  
Nexus · Singapore  
[LinkedIn](https://linkedin.com/in/cartertan)
