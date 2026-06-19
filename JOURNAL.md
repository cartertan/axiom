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

## Phase 3 — Orchestration + Action Execution
**Started:** 2026-06-19
**Target:** v0.3.0

### Session 1 — 2026-06-19
- Multi-agent orchestration engine (`src/core/orchestrator.py`): three modes — ensemble (parallel answers → synthesis), pipeline (draft → refine → polish), debate (independent answers → critique → judge). All calls go through `OllamaClient` and log to `BenchmarkLogger`. Execution is sequential (M5 Pro loads one model at a time); progress shown via callback.
- Orchestration config added to `models.yaml`: default model sets for each mode, and `multi_model_tasks` list (RFP_ANALYSIS, RESEARCH auto-default to ensemble if no `--mode` flag is given).
- `axiom.py` extended with `--mode ensemble|pipeline|debate|single` flag. Mode parsing extracts `--mode` from argv before command dispatch. Orchestration results show the final answer plus an expandable per-model summary.
- Safety gate (`src/actions/safety_gate.py`): `confirm_action(description, details_dict)` prints what AXIOM is about to do, prompts `yes/no`, returns `True` only on explicit confirm, logs every decision. Built before the email sender that depends on it.
- Task management agent (`src/agents/task_agent.py`): SQLite DB at `data/tasks.db`, schema `tasks(id, title, due_date, priority, status, project, customer, created_at)`. Natural-language intent parsed via `gemma4:e4b` → JSON → INSERT/SELECT/UPDATE. `axiom task add "…"` and `axiom task list` verified.
- Web search layer (`src/actions/web_search.py`): `WebSearch` using `ddgs` (renamed from `duckduckgo_search`); import uses try/except fallback for both package names. `search()` returns `{title, url, snippet}` list; `fetch_page()` strips scripts/styles/nav via BeautifulSoup, caps at 3000 words. Backend is pluggable — Brave or SearXNG can be swapped in via config.
- Research web agent (`src/agents/research_web_agent.py`): fetches top 3 pages in full, uses snippets for results 4-5; synthesises with `deepseek-r1:32b`; cites sources with `[Source N]` notation; distinguishes confirmed facts from interpretation. `axiom research "…"` command wired in.
- Email sender agent (`src/agents/email_sender_agent.py`): inherits from `EmailAgent` (reuses draft logic), extracts recipient via regex then model fallback, calls `SafetyGate.confirm_action()` with to/subject/body preview, sends via macOS Mail AppleScript on confirm only. Router gained `EMAIL_SEND` task type with updated classifier description.
- Benchmark runner (`src/benchmark/runner.py`): interactive quality-rated benchmark, composite score = quality×0.6 + speed×0.25 + token_eff×0.15. Wired into `axiom benchmark --task <type>`.
- Benchmark dashboard (`src/benchmark/dashboard.py`): reads CSV, writes `reports/benchmark_dashboard.html` (Chart.js bar chart, latency table, best-per-task summary) and `config/models_recommended.yaml`.
- Web UI mode selector: dropdown in footer, sent with every `/chat` POST. `app.py` routes to `Orchestrator` for non-single modes; `app.js` renders expandable per-model responses.
- GLM-5.2 evaluated: 1.51TB model, requires 256GB+ RAM — not viable on 64GB M5 Pro. Documented as optional API fallback only.

---
