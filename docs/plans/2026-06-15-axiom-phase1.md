# AXIOM — Phase 1 Implementation Plan
**Date:** 2026-06-15
**Version Target:** v0.1.0
**GitHub:** github.com/cartertan/axiom
**Status:** Ready to execute

---

## Phase 1 Goal

A working CLI assistant that:
- Knows who Carter is (profile + memory)
- Classifies task intent automatically
- Drafts emails in Carter's voice
- Summarises meeting notes in structured format
- Answers general questions fast
- Logs benchmark data on every run
- Persists memory across sessions

```bash
axiom "draft a follow-up email to the Singtel security team"
axiom "summarise these meeting notes: [paste]"
axiom "what is OCSP stapling and how do I explain it to a CIO?"
axiom benchmark --task email_draft
```

---

## Files to Create (in order of dependency)

```
axiom/
├── axiom.py                          # Entry point — wires everything together
├── README.md                         # Project description
├── CLAUDE.md                         # Claude Code instructions
├── JOURNAL.md                        # Build log
├── .gitignore                        # Excludes .env, chroma_db/, __pycache__
├── .env.example                      # Template for any future env vars
├── requirements.txt                  # Python dependencies
│
├── config/
│   └── models.yaml                   # Model assignments per task type
│
├── memory/
│   └── carter_profile.json           # Carter DNA — injected into every prompt
│
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── ollama_client.py          # Ollama API wrapper (chat + embeddings)
│   │   ├── profile.py                # Loads carter_profile.json
│   │   ├── memory.py                 # ChromaDB read/write + context retrieval
│   │   └── router.py                 # Intent classification → agent dispatch
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base_agent.py             # Abstract base class all agents inherit
│   │   ├── email_agent.py            # Email drafting via qwen3.6:27b
│   │   ├── meeting_agent.py          # Meeting summary via granite4.1:30b
│   │   └── general_agent.py          # Catch-all via gemma4:e4b
│   │
│   ├── benchmark/
│   │   ├── __init__.py
│   │   └── logger.py                 # Logs model/task/latency/tokens to CSV
│   │
│   └── interface/
│       ├── __init__.py
│       └── cli.py                    # Rich terminal UI — input/output formatting
│
└── data/
    └── benchmarks/                   # benchmark_results.csv lives here
```

---

## Task List (ordered by dependency)

---

### BLOCK A — Project Scaffold

**Task A1: Create the axiom project folder and git repo**

```bash
# macOS Terminal
cd ~/AI-Projects
mkdir axiom
cd axiom
git init
git checkout -b main
```

Verification: `ls ~/AI-Projects/axiom` shows empty folder. `git status` shows clean repo.

---

**Task A2: Create .gitignore**

Create `axiom/.gitignore` with:
```
__pycache__/
*.pyc
*.pyo
.env
memory/chroma_db/
data/
*.csv
.DS_Store
venv/
.venv/
```

Verification: `cat .gitignore` — all entries visible.

---

**Task A3: Create requirements.txt**

```
requests>=2.31.0
chromadb>=0.5.0
rich>=13.7.0
pyyaml>=6.0.1
python-dotenv>=1.0.0
```

Verification: `pip install -r requirements.txt --break-system-packages` runs without errors.

---

**Task A4: Create .env.example**

```
# AXIOM — Environment Variables
# No secrets required for local-only Ollama use
# Add API keys here if you ever enable cloud model fallback
# ANTHROPIC_API_KEY=your_key_here
OLLAMA_BASE_URL=http://localhost:11434
```

Verification: File exists. `.env` is in `.gitignore`.

---

**Task A5: Create folder structure**

```bash
mkdir -p config memory src/core src/agents src/benchmark src/interface data/benchmarks
touch src/__init__.py src/core/__init__.py src/agents/__init__.py
touch src/benchmark/__init__.py src/interface/__init__.py
```

Verification: `find . -type d` shows all directories. `find . -name "__init__.py"` shows 5 files.

---

### BLOCK B — Config & Profile

**Task B1: Create config/models.yaml**

```yaml
# AXIOM Model Assignments
# Updated automatically by benchmark engine (Phase 3)

ollama_base_url: "http://localhost:11434"

task_models:
  email_draft:
    primary: "qwen3.6:27b"
    fallback: "granite4.1:30b"
    thinking_mode: false

  meeting_summary:
    primary: "granite4.1:30b"
    fallback: "qwen3.6:27b"
    thinking_mode: false

  rfp_analysis:
    primary: "qwen3:30b"
    fallback: "deepseek-r1:32b"
    thinking_mode: true

  pki_qa:
    primary: "qwen3.6:27b"
    fallback: "granite4.1:30b"
    thinking_mode: false

  research:
    primary: "deepseek-r1:32b"
    fallback: "qwen3:30b"
    thinking_mode: false

  general:
    primary: "gemma4:e4b"
    fallback: "granite4.1:30b"
    thinking_mode: false

  router:
    primary: "gemma4:e4b"
    thinking_mode: false

benchmark_models:
  - "qwen3.6:27b"
  - "qwen3:30b"
  - "granite4.1:30b"
  - "deepseek-r1:32b"
  - "gemma4:e4b"
```

Verification: `python3 -c "import yaml; print(yaml.safe_load(open('config/models.yaml')))"` parses without error.

---

**Task B2: Create memory/carter_profile.json**

```json
{
  "name": "Carter Tan",
  "role": "Solutions Architect, AI Security Specialist",
  "company": "Nexus",
  "location": "Singapore",
  "years_experience": 18,
  "expertise": [
    "PKI", "digital identity", "certificate lifecycle management",
    "cybersecurity", "presales", "enterprise architecture",
    "cloud infrastructure", "AI and automation"
  ],
  "communication_style": "direct, structured, strategic",
  "preferred_tone": "professional but conversational — not stiff, not casual",
  "preferred_format": "bullet points and clear sections",
  "current_projects": ["presales-ai-platform", "axiom"],
  "typical_customers": ["telcos", "government", "banking", "energy", "manufacturing"],
  "customer_titles": ["CISOs", "CIOs", "enterprise architects", "security teams"],
  "products": ["PKI solutions", "certificate management", "digital trust platforms"],
  "goals": [
    "AI Architect journey June-November 2026",
    "Build portfolio of locally-run AI tools",
    "Become a leader in AI-driven cybersecurity"
  ],
  "running": {
    "current_target": "half marathon",
    "club": "SGRC",
    "approach": "data-driven, structured training"
  },
  "tools": ["Ollama", "Claude Code", "Python", "ChromaDB", "GitHub"],
  "values": ["continuous improvement", "long-term thinking", "precision", "efficiency"]
}
```

Verification: `python3 -c "import json; print(json.load(open('memory/carter_profile.json'))['name'])"` returns `Carter Tan`.

---

### BLOCK C — Core Layer

**Task C1: Create src/core/ollama_client.py**

Responsibility: All communication with Ollama API.
- `chat(model, messages, stream=False)` → returns response text
- `embed(text)` → returns embedding vector via nomic-embed-text
- `list_models()` → returns available models
- Handles connection errors gracefully with clear messages

Claude Code prompt:
```
Create src/core/ollama_client.py — an Ollama API wrapper class.
Requirements:
- OllamaClient class with base_url from config (default http://localhost:11434)
- chat(model, messages, stream=False) method — POST to /api/chat, returns response text
- embed(text) method — POST to /api/embeddings with model nomic-embed-text, returns vector list
- list_models() method — GET /api/tags, returns list of model name strings
- is_model_available(model_name) method — checks if model is in list
- All methods raise OllamaConnectionError with a clear message if Ollama is not running
- Include OllamaConnectionError as a custom exception class
- Use only requests library (no extra deps)
- Add docstrings to all methods
```

Verification:
```bash
python3 -c "
from src.core.ollama_client import OllamaClient
client = OllamaClient()
print(client.list_models())
"
```
Should print your model list.

---

**Task C2: Create src/core/profile.py**

Responsibility: Load and format carter_profile.json for injection into prompts.
- `load_profile()` → returns dict
- `format_for_prompt()` → returns a concise string summary for system prompts

Claude Code prompt:
```
Create src/core/profile.py.
Requirements:
- ProfileLoader class
- load_profile(path="memory/carter_profile.json") method — loads and returns dict
- format_for_prompt() method — returns a clean multi-line string summarising Carter
  for injection into LLM system prompts. Should cover: name, role, company, expertise,
  tone, typical customers, preferred format. Keep it under 200 words.
- Cache the loaded profile (don't re-read file on every call)
- Handle FileNotFoundError with a clear message
```

Verification:
```bash
python3 -c "
from src.core.profile import ProfileLoader
p = ProfileLoader()
print(p.format_for_prompt())
"
```
Should print a clean profile summary.

---

**Task C3: Create src/core/memory.py**

Responsibility: ChromaDB episodic memory — store and retrieve past interactions.
- `store_interaction(task_type, summary, entities, model_used)` → saves to ChromaDB
- `retrieve_context(query, n_results=3)` → returns relevant past interactions as string
- `clear_memory()` → wipes collection (for testing)

Claude Code prompt:
```
Create src/core/memory.py.
Requirements:
- AxiomMemory class
- Uses chromadb with persistent client at memory/chroma_db/
- Collection name: axiom_memory
- store_interaction(task_type, summary, entities=[], model_used="", metadata={}) method:
  - Embeds the summary using nomic-embed-text via OllamaClient
  - Stores in ChromaDB with metadata: task_type, model_used, timestamp (ISO format), entities (joined string)
  - Generates a unique ID using timestamp + task_type
- retrieve_context(query, n_results=3) method:
  - Embeds query using nomic-embed-text
  - Queries ChromaDB for n_results nearest neighbours
  - Returns formatted string of relevant past context for prompt injection
  - Returns empty string if no relevant context found
- clear_memory() method — deletes and recreates the collection
- Handle the case where ChromaDB collection doesn't exist yet (create on first use)
- Import OllamaClient from src.core.ollama_client
```

Verification:
```bash
python3 -c "
from src.core.memory import AxiomMemory
m = AxiomMemory()
m.store_interaction('email_draft', 'Drafted a follow-up email to Singtel security team about PKI refresh', ['Singtel', 'PKI'], 'qwen3.6:27b')
print(m.retrieve_context('Singtel email'))
"
```
Should return the stored interaction.

---

**Task C4: Create src/core/router.py**

Responsibility: Classify user input → task type → select agent + model.
- `classify(user_input)` → returns task type string
- Uses gemma4:e4b with a structured prompt — no regex hacks
- Returns one of: EMAIL_DRAFT, MEETING_SUMMARY, RFP_ANALYSIS, PKI_QA, RESEARCH, GENERAL, BENCHMARK

Claude Code prompt:
```
Create src/core/router.py.
Requirements:
- TaskRouter class
- classify(user_input) method:
  - Calls OllamaClient.chat() with model gemma4:e4b
  - System prompt: strict classifier — respond with ONLY one of these exact strings:
    EMAIL_DRAFT, MEETING_SUMMARY, RFP_ANALYSIS, PKI_QA, RESEARCH, GENERAL, BENCHMARK
  - User prompt: "Classify this task: {user_input}"
  - Strips whitespace from response, validates it's a known task type
  - Falls back to GENERAL if response is not a valid task type
- get_model_for_task(task_type, config) method:
  - Reads config/models.yaml
  - Returns (primary_model, fallback_model, thinking_mode) tuple
- Load models config once on init (pass config dict or path)
- Import OllamaClient from src.core.ollama_client
```

Verification:
```bash
python3 -c "
from src.core.router import TaskRouter
import yaml
config = yaml.safe_load(open('config/models.yaml'))
r = TaskRouter(config)
print(r.classify('draft a follow-up email to the Singtel security team'))
print(r.classify('summarise my meeting notes from the Maybank call'))
print(r.classify('what is certificate pinning and how does it relate to PKI'))
"
```
Should return: EMAIL_DRAFT, MEETING_SUMMARY, PKI_QA

---

### BLOCK D — Agents

**Task D1: Create src/agents/base_agent.py**

Responsibility: Abstract base class all agents inherit from.

Claude Code prompt:
```
Create src/agents/base_agent.py.
Requirements:
- BaseAgent abstract class
- Constructor takes: config (dict), profile_loader (ProfileLoader), memory (AxiomMemory), ollama_client (OllamaClient)
- Abstract method: run(user_input, task_type) → returns response string
- Helper method: build_system_prompt(task_description) → prepends Carter's profile
  to any task-specific system prompt
- Helper method: log_to_memory(task_type, user_input, response, model_used) →
  creates a short summary and calls memory.store_interaction()
- Use Python abc module for abstract base
```

Verification: `python3 -c "from src.agents.base_agent import BaseAgent; print('OK')"` — no import errors.

---

**Task D2: Create src/agents/email_agent.py**

Responsibility: Draft professional emails in Carter's voice using qwen3.6:27b.

Claude Code prompt:
```
Create src/agents/email_agent.py.
Requirements:
- EmailAgent class inheriting from BaseAgent
- run(user_input, task_type="EMAIL_DRAFT") method:
  1. Retrieve relevant memory context (past emails/customers mentioned)
  2. Build system prompt:
     - Carter's profile (from build_system_prompt())
     - Instruction: draft a professional email in Carter's voice
     - Tone: direct, confident, customer-focused
     - Format: subject line + body, no fluff, clear next step
     - Past context if available
  3. Call OllamaClient.chat() with qwen3.6:27b
  4. Log interaction to memory
  5. Return formatted email string
- Subject line should be on its own line prefixed with "Subject:"
```

Verification:
```bash
python3 -c "
import yaml
from src.core.ollama_client import OllamaClient
from src.core.profile import ProfileLoader
from src.core.memory import AxiomMemory
from src.agents.email_agent import EmailAgent
config = yaml.safe_load(open('config/models.yaml'))
client = OllamaClient()
profile = ProfileLoader()
memory = AxiomMemory()
agent = EmailAgent(config, profile, memory, client)
print(agent.run('draft a follow-up email to the Singtel security team about the PKI refresh proposal'))
"
```
Should return a complete, professional email.

---

**Task D3: Create src/agents/meeting_agent.py**

Responsibility: Summarise meeting notes into structured sections using granite4.1:30b.

Claude Code prompt:
```
Create src/agents/meeting_agent.py.
Requirements:
- MeetingAgent class inheriting from BaseAgent
- run(user_input, task_type="MEETING_SUMMARY") method:
  1. Build system prompt instructing structured summary output
  2. Required output sections:
     ## Meeting Summary
     **Date:** [extract or "Not specified"]
     **Attendees:** [list]
     **Key Decisions:** [bullet list]
     **Action Items:** [bullet list with owner if mentioned]
     **Next Steps:** [bullet list]
     **Follow-up Date:** [extract or "TBD"]
  3. Call OllamaClient.chat() with granite4.1:30b
  4. Log to memory
  5. Return formatted summary
```

Verification:
```bash
python3 -c "
import yaml
from src.core.ollama_client import OllamaClient
from src.core.profile import ProfileLoader
from src.core.memory import AxiomMemory
from src.agents.meeting_agent import MeetingAgent
config = yaml.safe_load(open('config/models.yaml'))
agent = MeetingAgent(config, ProfileLoader(), AxiomMemory(), OllamaClient())
test_notes = 'Met with John from Maybank and Sarah from IT. Discussed PKI deployment timeline. John wants certs deployed by Q3. Sarah needs HSM spec by next Friday. We agreed to send proposal by Monday.'
print(agent.run(test_notes))
"
```
Should return a clean structured summary.

---

**Task D4: Create src/agents/general_agent.py**

Responsibility: Fast catch-all agent for general questions using gemma4:e4b.

Claude Code prompt:
```
Create src/agents/general_agent.py.
Requirements:
- GeneralAgent class inheriting from BaseAgent
- run(user_input, task_type="GENERAL") method:
  1. Retrieve memory context
  2. Build system prompt with Carter's profile + instruction to be a
     concise, direct AI assistant for a cybersecurity solutions architect
  3. Call OllamaClient.chat() with gemma4:e4b
  4. Log to memory
  5. Return response
- This agent should respond in under 10 seconds on M5 Pro
```

Verification:
```bash
python3 -c "
import yaml
from src.core.ollama_client import OllamaClient
from src.core.profile import ProfileLoader
from src.core.memory import AxiomMemory
from src.agents.general_agent import GeneralAgent
config = yaml.safe_load(open('config/models.yaml'))
agent = GeneralAgent(config, ProfileLoader(), AxiomMemory(), OllamaClient())
print(agent.run('what is OCSP stapling and how do I explain it to a CIO?'))
"
```
Should return a clear, concise answer quickly.

---

### BLOCK E — Benchmark Logger

**Task E1: Create src/benchmark/logger.py**

Responsibility: Log model/task/latency/tokens to CSV after every agent run.

Claude Code prompt:
```
Create src/benchmark/logger.py.
Requirements:
- BenchmarkLogger class
- log(task_type, model, prompt_length, response_length, latency_seconds) method:
  - Appends a row to data/benchmarks/benchmark_results.csv
  - CSV columns: timestamp, task_type, model, prompt_chars, response_chars,
    latency_seconds, tokens_per_second (response_chars/latency if latency > 0)
  - Creates file with header row if it doesn't exist
  - Creates data/benchmarks/ directory if missing
- get_summary() method:
  - Reads CSV and returns dict of {model: {task: avg_latency}} for quick reporting
- Use only csv and datetime from stdlib (no pandas in Phase 1)
```

Verification:
```bash
python3 -c "
from src.benchmark.logger import BenchmarkLogger
bl = BenchmarkLogger()
bl.log('email_draft', 'qwen3.6:27b', 250, 800, 12.4)
bl.log('meeting_summary', 'granite4.1:30b', 400, 600, 8.1)
print(bl.get_summary())
"
```
CSV file should appear at `data/benchmarks/benchmark_results.csv`.

---

### BLOCK F — CLI Interface

**Task F1: Create src/interface/cli.py**

Responsibility: Rich terminal UI — formats AXIOM's input/output beautifully.

Claude Code prompt:
```
Create src/interface/cli.py.
Requirements:
- Use the Rich library for all terminal output
- AxiomCLI class
- print_banner() method — prints AXIOM name + tagline in a styled panel:
    ╔══════════════════════════════╗
    ║  AXIOM                       ║
    ║  The reasoning behind every  ║
    ║  decision.                   ║
    ╚══════════════════════════════╝
- print_response(response, task_type, model, latency) method:
  - Shows task type and model used in dim text above response
  - Response in a Rich Panel with appropriate colour per task type:
    EMAIL_DRAFT = blue, MEETING_SUMMARY = green, PKI_QA = yellow,
    GENERAL = white, RESEARCH = magenta, RFP_ANALYSIS = red
  - Shows latency in dim text below
- print_error(message) method — red panel with error message
- print_thinking() method — shows a spinner while model is running
- get_input(prompt="axiom> ") method — styled input prompt
```

Verification:
```bash
python3 -c "
from src.interface.cli import AxiomCLI
cli = AxiomCLI()
cli.print_banner()
cli.print_response('This is a test response', 'EMAIL_DRAFT', 'qwen3.6:27b', 3.2)
cli.print_error('Test error message')
"
```
Should display styled terminal output.

---

### BLOCK G — Entry Point

**Task G1: Create axiom.py**

Responsibility: Main entry point — wires all components together.

Claude Code prompt:
```
Create axiom.py — the main AXIOM entry point.
Requirements:
- Load config from config/models.yaml
- Initialise: OllamaClient, ProfileLoader, AxiomMemory, TaskRouter, BenchmarkLogger, AxiomCLI
- Parse sys.argv:
  Case 1: `python axiom.py "some task"` — single task mode
    1. Print banner
    2. Classify task with router
    3. Select and run appropriate agent
    4. Print response with CLI
    5. Log to benchmark logger
  Case 2: `python axiom.py benchmark --task email_draft` — benchmark mode
    1. Prompt user for a test prompt (or use a default)
    2. Run the prompt against ALL models in benchmark_models list
    3. Time each run
    4. Print a comparison table with Rich
    5. Log all results to CSV
  Case 3: No arguments — interactive mode
    1. Print banner
    2. Loop: get input → classify → run agent → print response
    3. Exit on 'quit' or Ctrl+C
- Agent selection logic:
  EMAIL_DRAFT → EmailAgent
  MEETING_SUMMARY → MeetingAgent
  RFP_ANALYSIS → GeneralAgent (placeholder until Phase 2)
  PKI_QA → GeneralAgent (placeholder until Phase 2)
  RESEARCH → GeneralAgent (placeholder until Phase 2)
  GENERAL → GeneralAgent
- Wrap everything in try/except — print friendly error via CLI on failure
- Include OllamaConnectionError handling with "Is Ollama running? Try: ollama serve"
```

Verification (all three modes):
```bash
python3 axiom.py "draft a follow-up email to the Singtel security team"
python3 axiom.py "summarise these notes: Met John from Maybank. Agreed to send PKI proposal by Friday."
python3 axiom.py benchmark --task email_draft
python3 axiom.py  # interactive mode — type a question, then quit
```

---

### BLOCK H — Documentation & Git

**Task H1: Create README.md**

Content to include:
- Project name AXIOM with tagline
- What it does (one paragraph)
- Phase 1 capabilities list
- Requirements section (Python 3.11+, Ollama, model list)
- Installation steps
- Usage examples (all three modes)
- Project structure tree
- Model stack table
- Roadmap (5 phases)
- Author + LinkedIn

---

**Task H2: Create CLAUDE.md**

Claude Code instructions for this project:
```markdown
# AXIOM — Claude Code Instructions

## Project Overview
AXIOM is a locally-run personal AI assistant for Carter Tan.
All LLM calls go to Ollama at http://localhost:11434.
No cloud API calls. No hardcoded secrets.

## Architecture Rules
- All Ollama calls go through src/core/ollama_client.py only
- All memory reads/writes go through src/core/memory.py only
- New agents must inherit from src/agents/base_agent.py
- Config changes go in config/models.yaml — not hardcoded

## Before Making Changes
1. Read the relevant src/ file first
2. Make one change at a time
3. Test with the verification command in the plan
4. Do not modify more than 2 files per task

## Testing
Run: python3 axiom.py "test prompt here"
Run: python3 -m pytest tests/ (Phase 2+)

## Git
Commit after each working task with: git commit -m "feat: [description]"
```

---

**Task H3: Create JOURNAL.md**

```markdown
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
```

---

**Task H4: Commit and push to GitHub**

```bash
cd ~/AI-Projects/axiom
git add .
git commit -m "feat: AXIOM v0.1.0 — Phase 1 complete

- CLI assistant with intent routing via gemma4:e4b
- Email agent (qwen3.6:27b)
- Meeting summary agent (granite4.1:30b)
- General agent (gemma4:e4b)
- Persistent memory (ChromaDB)
- Carter DNA profile (carter_profile.json)
- Benchmark logger (CSV)
- Rich terminal UI
"
git tag v0.1.0
git remote add origin https://github.com/cartertan/axiom.git
git push -u origin main --tags
```

---

## Phase 1 Success Criteria (Verification Checklist)

Run all of these before declaring v0.1.0 complete:

```bash
# 1. Email drafting
python3 axiom.py "draft a follow-up email to the Singtel security team about the PKI refresh"
# PASS if: returns Subject: line + professional email body in < 60 seconds

# 2. Meeting summary
python3 axiom.py "summarise these meeting notes: Met with John from Maybank and Sarah from IT. Discussed PKI deployment timeline. John wants certs deployed by Q3. Sarah needs HSM spec by next Friday. We agreed to send proposal by Monday."
# PASS if: returns structured summary with all 6 sections

# 3. General Q&A
python3 axiom.py "what is OCSP stapling and how do I explain it to a CIO?"
# PASS if: returns clear explanation in < 15 seconds

# 4. Memory persistence
python3 axiom.py "I just spoke to the Singtel team about their PKI project"
# exit, then:
python3 axiom.py "what do you know about Singtel?"
# PASS if: AXIOM references the previous interaction

# 5. Benchmark mode
python3 axiom.py benchmark --task email_draft
# PASS if: runs all models, prints comparison table, CSV file exists

# 6. Interactive mode
python3 axiom.py
# PASS if: banner displays, prompt appears, responds to input, exits on 'quit'

# 7. GitHub
# PASS if: github.com/cartertan/axiom is public with code + README
```

---

## Execution Order Summary

```
A1 → A2 → A3 → A4 → A5    # Scaffold
B1 → B2                     # Config + Profile
C1 → C2 → C3 → C4          # Core layer (dependency order: client → profile → memory → router)
D1 → D2 → D3 → D4          # Agents (base first, then email, meeting, general)
E1                           # Benchmark logger
F1                           # CLI
G1                           # Entry point (last — wires everything)
H1 → H2 → H3 → H4          # Docs + Git
```

Total tasks: 20
Estimated time at deep build pace: 2–3 sessions

