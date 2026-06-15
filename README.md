# AXIOM
**The reasoning behind every decision.**

AXIOM is a locally-run personal AI assistant built for Carter Tan — a Solutions Architect specialising in PKI and AI security. It runs entirely on-device via Ollama, with no cloud calls and no data leaving your machine. AXIOM classifies your intent, routes it to the right model, drafts emails in your voice, summarises meeting notes in structured format, answers technical questions fast, and logs benchmark data on every run. Memory persists across sessions via ChromaDB.

---

## Phase 1 Capabilities

- **Email drafting** — professional emails in Carter's voice (qwen3.6:27b)
- **Meeting summaries** — structured 6-section output from raw notes (granite4.1:30b)
- **General Q&A** — fast answers for cybersecurity and architecture questions (gemma4:e4b)
- **Intent routing** — automatic task classification, no manual flags needed (gemma4:e4b)
- **Persistent memory** — ChromaDB episodic memory across sessions (nomic-embed-text)
- **Benchmark mode** — compare all models on any task, logs to CSV
- **Rich terminal UI** — colour-coded output panels, task/model/latency metadata

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

---

## Project Structure

```
axiom/
├── axiom.py                    # Entry point
├── config/models.yaml          # Model assignments per task
├── memory/carter_profile.json  # Carter DNA — injected into every prompt
├── src/
│   ├── core/
│   │   ├── ollama_client.py    # All Ollama API calls
│   │   ├── profile.py          # Profile loader
│   │   ├── memory.py           # ChromaDB read/write
│   │   └── router.py           # Intent classification
│   ├── agents/
│   │   ├── base_agent.py       # Abstract base class
│   │   ├── email_agent.py      # Email drafting
│   │   ├── meeting_agent.py    # Meeting summaries
│   │   └── general_agent.py    # General Q&A
│   ├── benchmark/
│   │   └── logger.py           # CSV benchmark logger
│   └── interface/
│       └── cli.py              # Rich terminal UI
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

| Phase | Focus |
|---|---|
| **v0.1.0** | CLI assistant — routing, email, meetings, general Q&A, memory, benchmarks |
| **v0.2.0** | RFP analysis agent + PKI Q&A agent with deep domain prompts |
| **v0.3.0** | Automatic model selection via benchmark feedback loop |
| **v0.4.0** | Document ingestion — analyse RFPs, tenders, security specs |
| **v0.5.0** | Web UI dashboard + Strava integration for training log analysis |

---

## Author

**Carter Tan** — Solutions Architect, AI Security Specialist  
Nexus · Singapore  
[LinkedIn](https://linkedin.com/in/cartertan)
