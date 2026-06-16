# AXIOM — Phase 2 Implementation Plan
**Date:** 2026-06-15
**Version Target:** v0.2.0
**Branch:** phase-2-websuite
**Status:** Ready to execute today

---

## Phase 2 Goal

Transform AXIOM from a 3-agent CLI tool into a full work suite with:
- A consistent AXIOM personality across all agents
- Three new work agents: RFP, PKI Q&A, Research
- A browser-based chat interface (FastAPI + HTML/JS)
- PDF and notes file upload
- A PKI knowledge base with RAG retrieval

By end of Phase 2:
```bash
# CLI still works
axiom "analyse this RFP: [paste]"
axiom "what is OCSP stapling?"

# AND a web interface
python3 server.py
# → open http://localhost:8000 → chat with AXIOM in browser
```

---

## Pre-Build — Setup (do this first)

### Step 0.1: Create the feature branch
```bash
cd ~/AI-Projects/axiom
git checkout main
git pull origin main
git checkout -b phase-2-websuite
```

### Step 0.2: Install Phase 2 dependencies
```bash
pip install fastapi uvicorn python-multipart pdfplumber jinja2 --break-system-packages
```

### Step 0.3: Update requirements.txt
Add to existing requirements.txt:
```
fastapi>=0.110.0
uvicorn>=0.29.0
python-multipart>=0.0.9
pdfplumber>=0.11.0
jinja2>=3.1.0
```

Verification: `pip list | grep -i fastapi` shows fastapi installed.

---

## BLOCK I — AXIOM Personality Layer

**Task I1: Create config/personality.yaml**

```yaml
# AXIOM Personality Definition
identity: "AXIOM — Carter Tan's personal AI assistant"

character:
  - "Calm, precise, and direct"
  - "Occasional dry wit, never forced"
  - "Proactive — volunteers relevant information"
  - "Never sycophantic"

forbidden_phrases:
  - "Certainly!"
  - "Great question!"
  - "Of course!"
  - "I'd be happy to!"

rules:
  - "Give the shortest complete answer unless depth is requested"
  - "Address Carter by name occasionally, not every response"
  - "If you don't know something, say so directly"
  - "You are not a chatbot. You are an intelligent assistant."
```

Verification: `python3 -c "import yaml; print(yaml.safe_load(open('config/personality.yaml'))['identity'])"`

---

**Task I2: Create src/core/personality.py**

Claude Code prompt:
```
Create src/core/personality.py.
Requirements:
- PersonalityLayer class
- Loads config/personality.yaml
- get_personality_prompt() method — returns a formatted string block
  describing AXIOM's identity, character, forbidden phrases, and rules
  for injection into every agent's system prompt
- Cache the loaded config
- This will be called by base_agent.build_system_prompt()
```

Verification:
```bash
python3 -c "
from src.core.personality import PersonalityLayer
p = PersonalityLayer()
print(p.get_personality_prompt())
"
```

---

**Task I3: Update src/agents/base_agent.py to inject personality**

Claude Code prompt:
```
Update src/agents/base_agent.py.
Modify build_system_prompt() so it prepends the AXIOM personality block
(from PersonalityLayer.get_personality_prompt()) BEFORE Carter's profile.
Order: [AXIOM personality] → [Carter profile] → [task-specific instructions].
Add PersonalityLayer to the constructor.
Make sure all existing agents still work after this change.
```

Verification: Re-run an existing agent test:
```bash
python3 axiom.py "draft a quick email to confirm a meeting"
# Should still work, now with AXIOM personality (no "Certainly!" etc.)
```

---

## BLOCK J — PKI Knowledge Base + RAG

**Task J1: Create the knowledge folder and seed content**

```bash
mkdir -p knowledge/pki knowledge/products
```

Create a few starter PKI markdown files in knowledge/pki/:
- ocsp.md, crl.md, certificate-lifecycle.md, hsm.md, pqc.md

Claude Code prompt:
```
Create 5 starter knowledge files in knowledge/pki/ covering core PKI topics:
ocsp.md, crl.md, certificate-lifecycle.md, hsm.md, post-quantum-crypto.md
Each should be 200-400 words, technically accurate, written for a presales
solutions architect to reference when answering customer questions.
These will be indexed for RAG retrieval.
```

Verification: `ls knowledge/pki/` shows 5 markdown files.

---

**Task J2: Create src/rag/indexer.py**

Claude Code prompt:
```
Create src/rag/indexer.py.
Requirements:
- PKIIndexer class
- Reuses the proven RAG pattern: chunk → clean → embed → store in ChromaDB
- Collection name: axiom_pki_knowledge (separate from axiom_memory)
- index_knowledge_base(path="knowledge/pki/") method:
  - Reads all .md files
  - Chunks text (target ~300 words per chunk, preserve paragraph boundaries)
  - Cleans chunks: strip non-ASCII, normalise whitespace, skip chunks under 20 words
  - Embeds each chunk via OllamaClient.embed() using nomic-embed-text
  - Stores in ChromaDB with metadata: source_file, chunk_index
  - Prints progress (X chunks indexed from Y files)
- rebuild() method: explicitly calls client.delete_collection() before reindexing
  (the --rebuild flag alone silently reuses the old collection)
- Use the /api/embeddings endpoint pattern, not /api/generate
```

Verification:
```bash
python3 -c "
from src.rag.indexer import PKIIndexer
idx = PKIIndexer()
idx.rebuild()
"
```
Should print chunks indexed.

---

**Task J3: Create src/rag/retriever.py**

Claude Code prompt:
```
Create src/rag/retriever.py.
Requirements:
- PKIRetriever class
- retrieve(query, n_results=4) method:
  - Embeds query via nomic-embed-text
  - Queries axiom_pki_knowledge collection
  - Returns list of relevant chunks with source attribution
  - Returns formatted context string for prompt injection
- Handle empty collection gracefully (return message to run indexer first)
```

Verification:
```bash
python3 -c "
from src.rag.retriever import PKIRetriever
r = PKIRetriever()
print(r.retrieve('how does OCSP stapling work'))
"
```

---

## BLOCK K — New Agents

**Task K1: Create src/agents/rfp_agent.py**

Claude Code prompt:
```
Create src/agents/rfp_agent.py.
Requirements:
- RFPAgent class inheriting from BaseAgent
- Uses qwen3:30b with thinking_mode=true (from config)
- run(user_input, task_type="RFP_ANALYSIS") method:
  1. Retrieve relevant memory context
  2. Build system prompt: analyse the RFP text, extract:
     - Key requirements (numbered list)
     - Compliance items (must-have vs nice-to-have)
     - Potential gaps or risks
     - Recommended response strategy
  3. Call OllamaClient.chat() with qwen3:30b
  4. Log to memory
  5. Return structured analysis
- Reuse RFP analysis patterns from Carter's rfp-analyzer project where sensible
```

Verification:
```bash
python3 axiom.py "analyse this RFP requirement: The solution must support automated certificate lifecycle management with ACME protocol, integrate with existing HSM infrastructure, and provide 99.99% uptime SLA."
```

---

**Task K2: Create src/agents/pki_agent.py**

Claude Code prompt:
```
Create src/agents/pki_agent.py.
Requirements:
- PKIAgent class inheriting from BaseAgent
- Uses qwen3.6:27b
- Constructor also takes a PKIRetriever instance
- run(user_input, task_type="PKI_QA") method:
  1. Retrieve relevant PKI knowledge via PKIRetriever.retrieve()
  2. Build system prompt: answer the PKI question using the retrieved context,
     written for a presales architect to explain to a customer (CIO/CISO level)
  3. If retrieved context is empty, answer from model knowledge but note that
  4. Call OllamaClient.chat() with qwen3.6:27b
  5. Log to memory
  6. Return answer with source citations where context was used
```

Verification:
```bash
python3 axiom.py "explain OCSP stapling and why it matters for a bank's TLS infrastructure"
```

---

**Task K3: Create src/agents/research_agent.py**

Claude Code prompt:
```
Create src/agents/research_agent.py.
Requirements:
- ResearchAgent class inheriting from BaseAgent
- Uses deepseek-r1:32b
- run(user_input, task_type="RESEARCH") method:
  1. Retrieve memory context
  2. Build system prompt: provide structured analytical research on the topic:
     - Overview
     - Key players / technologies / considerations
     - Strategic implications for a PKI/security solutions architect
     - Recommended next steps
  3. Call OllamaClient.chat() with deepseek-r1:32b
  4. Log to memory
  5. Return structured research
  NOTE: This is Phase 2 — model-knowledge research only.
  Web search comes in Phase 3 (ResearchWebAgent).
```

Verification:
```bash
python3 axiom.py "research the competitive landscape for post-quantum cryptography migration tools"
```

---

**Task K4: Update axiom.py to route to new agents**

Claude Code prompt:
```
Update axiom.py agent selection logic.
Replace the Phase 1 placeholders:
  RFP_ANALYSIS → RFPAgent (was GeneralAgent)
  PKI_QA → PKIAgent (was GeneralAgent) — pass it a PKIRetriever instance
  RESEARCH → ResearchAgent (was GeneralAgent)
Keep EMAIL_DRAFT, MEETING_SUMMARY, GENERAL as they are.
Initialise PKIRetriever once at startup and pass to PKIAgent.
Make sure all three CLI modes (single, benchmark, interactive) still work.
```

Verification: Run all task types via CLI, confirm correct agent fires.

---

## BLOCK L — Web Interface

**Task L1: Create src/interface/web/app.py**

Claude Code prompt:
```
Create src/interface/web/app.py — a FastAPI application.
Requirements:
- FastAPI app
- Initialise all AXIOM components once at startup (router, agents, memory, etc.)
- Routes:
  GET  /          → serve the chat HTML page (Jinja2 template)
  POST /chat      → accept {message: str}, classify, run agent, return {response, task_type, model, latency}
  POST /upload    → accept a PDF file, extract text with pdfplumber, return extracted text
  GET  /history   → return recent interactions from memory
- Enable CORS for local dev
- All processing stays local (calls Ollama)
- Return clear JSON errors if Ollama is down
```

Verification:
```bash
python3 -m uvicorn src.interface.web.app:app --reload --port 8000
# In browser: http://localhost:8000 should load
# curl test:
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{"message":"what is a root CA?"}'
```

---

**Task L2: Create the chat HTML interface**

Claude Code prompt:
```
Create src/interface/web/templates/index.html plus
src/interface/web/static/style.css and static/app.js.
Requirements:
- Clean dark-themed chat interface (AXIOM branding, the tagline)
- Message history area (user messages right, AXIOM left)
- Each AXIOM response shows a small badge: task_type + model + latency
- Text input + send button (Enter to send)
- File upload button for PDFs — extracted text gets added to the input
- Colour-code response badges by task type (match the CLI colours:
  EMAIL_DRAFT blue, MEETING_SUMMARY green, PKI_QA yellow, RESEARCH magenta,
  RFP_ANALYSIS red, GENERAL grey)
- A typing indicator while AXIOM is thinking
- Vanilla JS only (no React build step needed) — fetch() to /chat and /upload
- Keep it clean and professional, not flashy
```

Verification: Reload http://localhost:8000, send a message, confirm response appears with badge.

---

**Task L3: Create server.py entry point**

Claude Code prompt:
```
Create server.py in the project root.
Requirements:
- Simple entry point that launches the FastAPI app via uvicorn
- Prints the AXIOM banner and the URL (http://localhost:8000)
- Checks Ollama is reachable before starting — clear error if not
- Runs on port 8000, host 127.0.0.1 (local only, never 0.0.0.0)
```

Verification:
```bash
python3 server.py
# Banner prints, server starts, browser loads the chat UI
```

---

## BLOCK M — Documentation & Git

**Task M1: Update README.md**
- Add the 5-layer Tony Stark vision
- Update roadmap (Phase 1 ✅, Phase 2 in progress, 3/4/5 planned)
- Add web UI usage instructions
- Add PKI knowledge base section
- Screenshot of the web interface

**Task M2: Update JOURNAL.md**
Add Phase 2 entry: personality layer, RAG knowledge base, web UI, new agents.

**Task M3: Commit and merge**
```bash
cd ~/AI-Projects/axiom
git add .
git commit -m "feat: AXIOM v0.2.0 — Phase 2 work suite

- AXIOM personality layer across all agents
- RFP, PKI Q&A, and Research agents
- PKI knowledge base with RAG retrieval
- FastAPI web interface with chat UI
- PDF upload and text extraction
"
git checkout main
git merge phase-2-websuite
git tag v0.2.0
git push origin main --tags
```

---

## Phase 2 Success Criteria

```bash
# 1. Personality — no sycophantic phrases
python3 axiom.py "thanks for the help"
# PASS if: response is natural, no "Of course!" / "Certainly!"

# 2. RFP agent
python3 axiom.py "analyse this RFP: solution must support ACME, integrate with HSM, 99.99% uptime"
# PASS if: structured analysis with requirements, gaps, strategy

# 3. PKI agent with RAG
python3 axiom.py "explain OCSP stapling for a CISO"
# PASS if: accurate answer drawing on knowledge base

# 4. Research agent
python3 axiom.py "research post-quantum crypto migration approaches"
# PASS if: structured analytical research

# 5. Web UI
python3 server.py
# PASS if: browser loads, chat works, badges show, PDF upload works

# 6. CLI still works (regression check)
python3 axiom.py "draft an email"
python3 axiom.py benchmark --task email_draft
# PASS if: both still function

# 7. GitHub
# PASS if: v0.2.0 tagged and pushed
```

---

## Execution Order

```
0.1 → 0.2 → 0.3              # Branch + deps
I1 → I2 → I3                 # Personality layer
J1 → J2 → J3                 # PKI knowledge + RAG
K1 → K2 → K3 → K4            # New agents
L1 → L2 → L3                 # Web interface
M1 → M2 → M3                 # Docs + merge
```

Total tasks: 16
Estimated: 1 focused session (3-4 hours with Claude Code)

