# AXIOM — Build Journal

## Phase 1 — Foundation + CLI
**Started:** 2026-06-15
**Target:** v0.1.0

### Session 1 — 2026-06-15
- Design approved
- Model stack updated and confirmed
- Agent named AXIOM
- Phase 1 implementation plan written

### Build Log
[Add entries here as you build]

---

## Phase 2 — Work Suite
**Started:** 2026-06-16
**Target:** v0.2.0

### Session 1 — 2026-06-16
- Personality layer added: `config/personality.yaml` + `PersonalityLayer`, injected into every agent's system prompt ahead of Carter's profile via `base_agent.build_system_prompt()`
- PKI knowledge base built: 5 reference Markdown files in `knowledge/pki/`, chunked/cleaned/embedded by `PKIIndexer` into a dedicated ChromaDB collection (`axiom_pki_knowledge`), retrieved by `PKIRetriever` with source attribution
- Three new agents: `RFPAgent` (qwen3:30b, thinking mode), `PKIAgent` (qwen3.6:27b + RAG), `ResearchAgent` (deepseek-r1:32b), wired into `axiom.py` routing
- Found and fixed a routing gap: the task classifier's system prompt gave the router model no category descriptions, so PKI questions were misclassified as GENERAL/RESEARCH instead of PKI_QA. Added brief per-category descriptions to `router.py`'s system prompt — fixed across all tested PKI phrasing
- Extended `OllamaClient.chat()` with a `think` parameter to support Ollama's native `think` API field, needed for RFP analysis's thinking-mode requirement
- Web interface shipped: FastAPI app (`src/interface/web/app.py`) with `/`, `/chat`, `/upload`, `/history`; dark-themed vanilla-JS chat UI with task-type badges, PDF upload via pdfplumber; `server.py` entry point with an Ollama reachability check before serving on `127.0.0.1:8000`
- Added `AxiomMemory.get_recent_interactions()` to back `/history` without bypassing the memory module
- All new components verified against real Ollama calls and a real browser (Playwright) session, not just imports — including a regression pass on Phase 1 CLI behavior

---
