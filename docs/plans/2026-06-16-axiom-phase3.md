# AXIOM — Phase 3 Implementation Plan
**Date:** 2026-06-16
**Version Target:** v0.3.0
**Branch:** phase-3-orchestration
**Status:** Ready to execute today

---

## Phase 3 Goal

Two big upgrades in one phase:

1. **Multi-Agent Orchestration Engine** — multiple models collaborate on a single
   task, in three selectable modes (ensemble, pipeline, debate), for the best result.

2. **Action Execution Layer** — AXIOM stops just drafting and starts DOING:
   task management, email sending (with safety gate), web research.

Plus the benchmark dashboard to prove which models/modes win.

By end of Phase 3:
```bash
axiom "analyse this RFP" --mode ensemble    # 3 models answer, AXIOM synthesises
axiom "draft proposal intro" --mode pipeline # models refine in sequence
axiom "should we use OCSP or CRL here" --mode debate  # models critique, converge
axiom task add "Follow up with Singtel by Friday"
axiom "send that email to John"              # drafts, reads back, sends on confirm
axiom research "Thales PKI telco strategy"   # live web search + synthesis
```

---

## Design Decisions (Locked)

- **Orchestration modes:** All three (ensemble, pipeline, debate) as selectable modes
- **Priority:** Quality first — sequential model loading is acceptable for best results
- **GLM-5.2:** NOT viable locally (1.51TB, needs 256GB+ RAM). Optional API fallback only.
- **Hardware reality:** M5 Pro loads one model at a time. Multi-model = sequential.
  AXIOM shows progress per model so the wait is transparent.

---

## Hardware Note: How Multi-Model Works on M5 Pro

Your 64GB M5 Pro runs one Ollama model at a time. For multi-model orchestration:
- AXIOM loads model A → gets response → unloads
- Loads model B → gets response → unloads
- Loads model C → gets response → unloads
- A synthesiser model combines them

This is SEQUENTIAL, not truly parallel. A 3-model ensemble takes roughly
3x a single call plus synthesis. For an RFP analysis that might mean 4-6 minutes.
That is the quality-first tradeoff you chose. AXIOM will show a progress
indicator per model so you always know where it is.

Tip: keep the model set small per task (2-3 models max) to keep waits sane.

---

## Pre-Build — Setup

### Step 0.1: Branch + dependencies
```bash
cd ~/AI-Projects/axiom
git checkout main && git pull origin main
git checkout -b phase-3-orchestration

pip install duckduckgo-search sqlite-utils beautifulsoup4 --break-system-packages
```

### Step 0.2: Update requirements.txt
```
duckduckgo-search>=3.9.0
sqlite-utils>=3.35
beautifulsoup4>=4.12.0
```

Verification: `pip list | grep -i duckduckgo` shows it installed.

---

## BLOCK N — Multi-Agent Orchestration Engine

**Task N1: Create src/core/orchestrator.py**

Claude Code prompt:
```
Create src/core/orchestrator.py — the multi-model orchestration engine.
Requirements:
- Orchestrator class
- Three methods, one per mode:

  run_ensemble(task_type, prompt, models, synthesiser_model):
    - Sends the same prompt to each model in `models` SEQUENTIALLY
      (M5 Pro runs one at a time)
    - Collects all responses with timing
    - Then calls synthesiser_model with a prompt that includes all responses
      and asks it to produce the single best answer, combining strengths
    - Returns {final, individual_responses, timings}

  run_pipeline(task_type, prompt, model_sequence):
    - Passes output of model 1 as input context to model 2, etc.
    - Each model is told what stage it is (draft / refine / polish)
    - Returns {final, stages, timings}

  run_debate(task_type, prompt, models, judge_model):
    - Round 1: each model answers independently
    - Round 2: each model sees the others' answers and critiques + revises
    - judge_model picks or synthesises the best final answer
    - Returns {final, round1, round2, timings}

- Show progress via a callback (print which model is running now)
- All calls go through OllamaClient
- Log every sub-call to BenchmarkLogger
- Each mode returns a structured result the CLI/web can render
```

Verification:
```bash
python3 -c "
import yaml
from src.core.ollama_client import OllamaClient
from src.core.orchestrator import Orchestrator
from src.benchmark.logger import BenchmarkLogger
config = yaml.safe_load(open('config/models.yaml'))
orch = Orchestrator(OllamaClient(), BenchmarkLogger())
result = orch.run_ensemble('general', 'In one sentence, what is a digital certificate?',
    ['qwen3.6:27b','granite4.1:30b'], 'qwen3:30b')
print(result['final'])
"
```
Should run both models then synthesise.

---

**Task N2: Add orchestration config to config/models.yaml**

Claude Code prompt:
```
Update config/models.yaml — add an orchestration section:

orchestration:
  ensemble:
    default_models: ["qwen3.6:27b", "qwen3:30b", "deepseek-r1:32b"]
    synthesiser: "qwen3:30b"
  pipeline:
    default_sequence: ["qwen3.6:27b", "granite4.1:30b", "qwen3:30b"]
  debate:
    default_models: ["qwen3:30b", "deepseek-r1:32b"]
    judge: "qwen3.6:27b"

  # Which task types default to multi-model (quality-first)
  multi_model_tasks: ["RFP_ANALYSIS", "RESEARCH"]
  # Everything else stays single-model unless --mode is passed
```

Verification: yaml parses, orchestration keys present.

---

**Task N3: Wire orchestration into axiom.py**

Claude Code prompt:
```
Update axiom.py to support a --mode flag:
  --mode ensemble | pipeline | debate | single (default depends on task)

Logic:
- Parse --mode from argv
- If --mode given, route through Orchestrator with that mode
- If no --mode but task is in multi_model_tasks list, default to ensemble
- Otherwise single-model (existing behaviour)
- Print progress as each model runs (use the CLI's print_thinking with model name)
- Render the final answer plus an optional "show individual responses" summary

Keep all existing modes working (single task, benchmark, interactive).
```

Verification:
```bash
python3 axiom.py "analyse this RFP requirement: must support ACME and HSM integration" --mode ensemble
python3 axiom.py "explain the difference between OCSP and CRL" --mode debate
```

---

## BLOCK O — Action Execution Layer

**Task O1: Create src/actions/safety_gate.py**

Claude Code prompt:
```
Create src/actions/safety_gate.py.
Requirements:
- SafetyGate class
- confirm_action(description, details_dict) method:
  - Prints what AXIOM is about to do (the action description + key details)
  - Prompts the user: "Confirm? (yes/no)"
  - Returns True only on explicit "yes" / "y" / "confirm"
  - Returns False otherwise
- This gate MUST be called before any external/destructive action
  (send email, create calendar event, etc.)
- Log every confirmation decision to memory
```

Verification:
```bash
python3 -c "
from src.actions.safety_gate import SafetyGate
g = SafetyGate()
print(g.confirm_action('Send test email', {'to':'test@example.com','subject':'Hi'}))
"
# Type 'no' — should return False
```

---

**Task O2: Create src/agents/task_agent.py + SQLite store**

Claude Code prompt:
```
Create src/agents/task_agent.py.
Requirements:
- TaskAgent class inheriting from BaseAgent
- Uses a local SQLite DB at data/tasks.db (gitignored)
- Schema: tasks(id, title, due_date, priority, status, project, customer, created_at)
- Natural language commands parsed via gemma4:e4b into structured actions:
  - "add a task to follow up with Singtel by Friday" → INSERT
  - "what's on my plate today" / "list tasks" → SELECT pending
  - "mark the Singtel task done" → UPDATE status
- run(user_input) interprets intent, performs the DB action, returns confirmation
- Use sqlite3 from stdlib (no ORM needed)
- For ADD and DONE actions, no safety gate needed (local, non-destructive)
  but print clear confirmation of what was stored
```

Verification:
```bash
python3 axiom.py task add "Follow up with Singtel security team by Friday"
python3 axiom.py task list
```

---

**Task O3: Create src/actions/web_search.py + src/agents/research_web_agent.py**

Claude Code prompt:
```
Create src/actions/web_search.py:
- WebSearch class using duckduckgo-search (free, no API key)
- search(query, max_results=5) → returns list of {title, url, snippet}
- fetch_page(url) → returns cleaned text via requests + beautifulsoup4
  (strip scripts/styles, return readable text, cap at ~3000 words)

Create src/agents/research_web_agent.py:
- ResearchWebAgent inheriting from BaseAgent, uses deepseek-r1:32b
- run(user_input):
  1. Use WebSearch.search() to get top results
  2. Fetch the 2-3 most relevant pages
  3. Synthesise findings with deepseek-r1:32b, with source citations
  4. Distinguish confirmed facts (from sources) vs interpretation
  5. Log to memory
- This is the LIVE web version (Phase 2 ResearchAgent was model-knowledge only)
```

Verification:
```bash
python3 axiom.py research "latest developments in post-quantum cryptography standards 2026"
```
Should search the web, fetch pages, return cited synthesis.

---

**Task O4: Create src/agents/email_sender_agent.py**

Claude Code prompt:
```
Create src/agents/email_sender_agent.py.
Requirements:
- EmailSenderAgent inheriting from EmailAgent (reuse drafting logic)
- Adds send capability via macOS Mail using AppleScript (osascript subprocess)
- Flow:
  1. Draft the email (reuse parent EmailAgent.run)
  2. Extract recipient if mentioned, else ask
  3. Call SafetyGate.confirm_action() — read back to/subject/body summary
  4. Only on confirm: build AppleScript that creates and sends the message
     via macOS Mail, run via osascript
  5. Log the sent action to memory
- If recipient is missing or unclear, do NOT send — ask for clarification
- NEVER send without passing through SafetyGate
- Keep host local; this uses the Mac's own Mail app, no SMTP credentials needed
```

Verification (safe test — decline at the gate):
```bash
python3 axiom.py "send a follow-up email to test@example.com confirming our meeting"
# At the confirm prompt, type 'no' — verify it does NOT send
```

---

## BLOCK P — Benchmark Dashboard

**Task P1: Create src/benchmark/runner.py**

Claude Code prompt:
```
Create src/benchmark/runner.py.
Requirements:
- BenchmarkRunner class
- run_benchmark(task_type, prompt, models) method:
  - Sends prompt to each model, captures response + latency + token count
  - Prompts Carter to rate each response 1-5
  - Computes score = (quality*0.6) + (speed_score*0.25) + (token_eff*0.15)
    where speed_score and token_eff are normalised 0-1 across the models tested
  - Writes results to data/benchmarks/benchmark_results.csv
  - Returns ranked results
```

Verification:
```bash
python3 axiom.py benchmark --task pki_qa
```

---

**Task P2: Create src/benchmark/dashboard.py**

Claude Code prompt:
```
Create src/benchmark/dashboard.py.
Requirements:
- generate_dashboard() method reads data/benchmarks/benchmark_results.csv
- Produces reports/benchmark_dashboard.html — a self-contained HTML file:
  - Bar chart: average score per model per task type
  - Table: latency, tokens/sec, quality rating per model
  - "Recommended model per task" summary derived from scores
  - Use inline CSS + a lightweight chart approach (Chart.js via CDN or inline SVG)
- Also writes an updated config/models_recommended.yaml with the winning model
  per task (do NOT overwrite models.yaml automatically — write a separate file
  for Carter to review and merge)
```

Verification:
```bash
python3 -c "from src.benchmark.dashboard import generate_dashboard; generate_dashboard()"
open reports/benchmark_dashboard.html
```

---

## BLOCK Q — Web UI Update + Docs + Git

**Task Q1: Add orchestration mode selector to web UI**

Claude Code prompt:
```
Update src/interface/web/templates/index.html and static/app.js:
- Add a mode dropdown: Single / Ensemble / Pipeline / Debate
- Pass the selected mode to POST /chat
- Show per-model progress in the UI while orchestration runs
- For multi-model results, show the final answer with an expandable
  "see individual model responses" section
Update src/interface/web/app.py /chat route to accept and handle the mode param.
```

Verification: web UI shows mode selector, ensemble mode works in browser.

---

**Task Q2: Update README.md + JOURNAL.md**
- Document orchestration modes (ensemble/pipeline/debate)
- Document action layer (tasks, email send, web research)
- Note GLM-5.2 evaluation: powerful but 1.51TB, not viable on 64GB M5 Pro;
  documented as optional API fallback
- Add benchmark dashboard section
- Update roadmap: Phase 3 complete

**Task Q3: Commit, merge, tag**
```bash
cd ~/AI-Projects/axiom
git add .
git commit -m "feat: AXIOM v0.3.0 — orchestration + action execution

- Multi-agent orchestration engine (ensemble/pipeline/debate modes)
- Action execution layer: task management, email sending, web research
- Safety gate for all external actions
- Benchmark runner + HTML dashboard
- Web UI orchestration mode selector
- GLM-5.2 evaluated: not viable locally, documented as API fallback
"
git checkout main && git merge phase-3-orchestration
git tag v0.3.0
git push origin main --tags
git branch -d phase-3-orchestration
```

---

## Phase 3 Success Criteria

```bash
# 1. Ensemble mode — multiple models + synthesis
python3 axiom.py "analyse this RFP: must support ACME, HSM, 99.99% uptime" --mode ensemble
# PASS if: runs 3 models sequentially, shows progress, returns synthesised answer

# 2. Debate mode
python3 axiom.py "OCSP vs CRL for a high-traffic bank — which and why" --mode debate
# PASS if: 2 models answer, critique, judge produces final

# 3. Pipeline mode
python3 axiom.py "write a proposal opening for a telco PKI refresh" --mode pipeline
# PASS if: draft → refine → polish through 3 models

# 4. Task management
python3 axiom.py task add "Prepare Maybank proposal by Thursday"
python3 axiom.py task list
# PASS if: task stored in SQLite and listed

# 5. Web research
python3 axiom.py research "post-quantum cryptography migration 2026"
# PASS if: live web search, fetched pages, cited synthesis

# 6. Email send with safety gate
python3 axiom.py "send a meeting confirmation to test@example.com"
# PASS if: drafts, reads back, asks confirm — type 'no', verify NOT sent

# 7. Benchmark dashboard
python3 axiom.py benchmark --task pki_qa
python3 -c "from src.benchmark.dashboard import generate_dashboard; generate_dashboard()"
open reports/benchmark_dashboard.html
# PASS if: HTML dashboard renders with charts + recommendations

# 8. Regression — Phase 1 + 2 still work
python3 axiom.py "draft an email"
python3 server.py  # web UI loads
# PASS if: both still function
```

---

## Execution Order

```
0.1 → 0.2                  # Branch + deps
N1 → N2 → N3               # Orchestration engine (the headline feature)
O1 → O2 → O3 → O4          # Action layer (safety gate FIRST, then agents)
P1 → P2                    # Benchmark dashboard
Q1 → Q2 → Q3               # Web UI + docs + merge
```

Total tasks: 14
Estimated: 1 focused session (orchestration testing adds time due to sequential model loading)

---

## Important Build Notes for Claude Code

- Safety gate (O1) MUST be built before the email sender (O4) that depends on it
- Orchestration is sequential on this hardware — do not attempt true parallelism
  with threads; Ollama serialises model loads anyway on a single machine
- Email sending uses macOS Mail via osascript — no SMTP credentials, no secrets
- data/tasks.db and data/benchmarks/ stay gitignored
- Keep the safety gate in the loop for ALL external actions — never bypass
