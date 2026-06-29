# AXIOM — Phase 5 Implementation Plan
## Multi-Agent Council + Obsidian Brain + Voice UI + GLM-5.2 Cloud Escalation
**Date:** 2026-06-19
**Version Target:** v0.5.0
**Branch:** phase-5-council
**Status:** Ready to execute

---

## Phase 5 Goal

The biggest architectural leap yet. Four upgrades:

1. **Obsidian as AXIOM's living brain** — two-way: AXIOM reads your vault for
   context AND writes decisions, summaries, and meeting notes back into it.

2. **Multi-agent council** — specialist agents (architect, security, devil's
   advocate, reviewer) that question and challenge each other, plus a lead agent
   that delegates and synthesises. A full multi-agent framework, not just debate.

3. **GLM-5.2 cloud escalation** — high-complexity reasoning escalates to
   glm-5.2:cloud via Ollama Cloud, kept local-first and cost-controlled.

4. **Voice-enabled interactive UI** — upgrade the existing FastAPI web UI into a
   real conversational interface with voice in/out.

By end of Phase 5:
```bash
axiom council "Should we recommend OCSP stapling or short-lived certs for this bank?"
# -> architect, security, devil's advocate debate; reviewer synthesises;
#    decision written to Obsidian as a linked note

axiom council "Design a crypto-agile PQC migration for a national bank" --complex
# -> hard reasoning escalates to glm-5.2:cloud, degrades to local if cloud is down

axiom serve  # voice-enabled web UI with council + Obsidian
```

---

## Design Decisions (Locked)

- **Obsidian:** Two-way — read vault for context, write decisions/summaries back
- **Multi-agent:** Full framework — specialist roles + debate + hierarchical delegation
- **Voice UI:** Enhance the existing FastAPI web UI (don't rebuild) + add voice
- **GLM-5.2:** NOT local (1.51TB). Accessed as glm-5.2:cloud via Ollama Cloud,
  same ollama Python client. Start FREE tier. Cloud is fallback only.
- **Vault is source of truth:** Markdown files are the knowledge system;
  Obsidian is just the viewer. AXIOM works on the files directly.
- **Everything local-first:** vault on disk, models in Ollama, voice on-device,
  cloud only for high-complexity reasoning that earns it.

---

## Architecture: The Council Pattern

```
                    User question
                         |
                  +--------------+
                  |  LEAD AGENT  |  (qwen3:30b)
                  |  delegates   |
                  +------+-------+
            +------------+------------+
            v            v            v
     +-----------+ +----------+ +--------------+
     | ARCHITECT | | SECURITY | | DEVIL'S      |
     |  AGENT    | |  AGENT   | | ADVOCATE     |
     |qwen3.6:27b| |deepseek  | | qwen3:30b    |
     +-----+-----+ +----+-----+ +------+-------+
           |            |              |
           +------------+--------------+
                        v
                +--------------+      complexity > 60?
                |  REVIEWER    |----------------------+
                |  synthesises |                      v
                |  + critiques |              glm-5.2:cloud
                +------+-------+              (Ollama Cloud)
                       |                      fallback: local
                       v
              Final answer + decision
                       |
              Written to Obsidian vault
                  (linked note)
```

---

## Why Obsidian (Key Insight)

Your markdown files ARE the knowledge system — Obsidian is just the viewer.
AXIOM reads and writes plain .md files directly; Obsidian picks up changes live
with its graph, backlinks, and search. No plugin or API needed.

Provenance pattern: tag every AXIOM-written claim as [extracted], [inferred],
or [decision] so you always know what AXIOM knew vs. what it synthesised. Good
epistemic hygiene for a security architect.

---

## GLM-5.2 Cloud Strategy (consistent with CLM-OS)

GLM-5.2 is NOT run locally (1.51TB, needs 256GB+ RAM). It is accessed as
glm-5.2:cloud via Ollama Cloud, called through the SAME ollama Python client as
every local model — no separate SDK, no separate billing.

Escalation logic:
```
council sub-question -> complexity score 0-100
   score > 60 (or --complex)  ->  glm-5.2:cloud  (frontier reasoning)
   score <= 60                ->  local model (qwen3:30b / deepseek-r1:32b)
```

Cost posture: START on Ollama Cloud FREE tier. AXIOM's council is on-demand
(not scheduled loops), so it is unlikely to exhaust Free. Upgrade to Pro
($20/mo) only when usage actually hits the Free quota.

Caveat: Ollama Cloud has no uptime SLA (95% failure window April 2026). Fine as
fallback because local stays primary — if cloud is down, the council degrades
gracefully to a local reviewer. Never put GLM-5.2 on a time-sensitive path.

---

## Pre-Build — Setup

### Step 0.1: Branch
```bash
cd ~/AI-Projects/axiom
git checkout main && git pull origin main
git checkout -b phase-5-council
```

### Step 0.2: Create the Obsidian vault folder
```bash
mkdir -p ~/Obsidian/AXIOM-Brain/{decisions,meetings,research,daily,concepts}
```

### Step 0.3: Confirm Ollama Cloud access (validates the GLM-5.2 path)
```bash
ollama login
ollama run glm-5.2:cloud "Confirm you are GLM-5.2 and your context window size"
```
If it responds, your free-tier cloud escalation path is live.

### Step 0.4: Optional — file watching for live re-index
```bash
pip install watchdog --break-system-packages
```

---

## BLOCK W — Obsidian Brain (Two-Way)

**Task W1: Create src/brain/vault.py**

Claude Code prompt:
```
Create src/brain/vault.py.
Requirements:
- ObsidianVault class, vault_path from config (default ~/Obsidian/AXIOM-Brain/)
- READ methods:
  - read_note(relative_path) -> markdown content
  - search_notes(query) -> semantic search via nomic-embed-text + a vault
    ChromaDB collection (axiom_vault)
  - list_notes(folder=None) -> lists .md files
  - get_recent_notes(n=5) -> most recently modified notes
- WRITE methods:
  - write_note(folder, title, content, tags=[], links=[]) -> creates a .md file
    with Obsidian frontmatter (title, date, tags, provenance) and [[wikilinks]]
  - append_to_daily(content) -> appends to today's daily note (creates if missing)
  - write_decision(question, options, recommendation, rationale) ->
    structured decision note in decisions/ folder
- All writes include provenance frontmatter (extracted/inferred/decision)
- Pure markdown file I/O — no Obsidian API; Obsidian reads the files live
```

Verification:
```bash
python3 -c "
from src.brain.vault import ObsidianVault
v = ObsidianVault()
v.write_note('concepts', 'Test Concept', 'This is a test note from AXIOM.', tags=['test'])
print(v.list_notes('concepts'))
"
```

**Task W2: Create src/brain/vault_indexer.py + wire into memory**

Claude Code prompt:
```
Create src/brain/vault_indexer.py.
- Reuses the proven RAG pattern (chunk, clean, embed via nomic-embed-text)
- Indexes all vault .md files into ChromaDB collection axiom_vault
- rebuild() explicitly deletes the collection first
- Incremental mode: only re-index files modified since last run (track mtimes)
Update src/core/memory.py so retrieve_context() can optionally pull from BOTH
axiom_memory (episodic) AND axiom_vault (Obsidian knowledge).
```

Verification:
```bash
python3 -c "from src.brain.vault_indexer import VaultIndexer; VaultIndexer().rebuild()"
```

---

## BLOCK X — Multi-Agent Council

**Task X1: Create specialist roles in src/council/roles.py**

Claude Code prompt:
```
Create src/council/roles.py.
- Defines specialist agent roles, each with a distinct system-prompt persona:
  - ArchitectRole (qwen3.6:27b): solution design, integration, operational fit
  - SecurityRole (deepseek-r1:32b): threats, compliance, attack surface, risk
  - DevilsAdvocateRole (qwen3:30b): challenges assumptions, argues opposing case
  - ReviewerRole (qwen3:30b): synthesises all inputs, final recommendation + rationale
  - LeadRole (qwen3:30b): decomposes the question, decides which specialists to engage
- Each role is a class with get_system_prompt() layered on AXIOM personality + profile
- Models per role configurable in config/council.yaml
```

Verification: `python3 -c "from src.council.roles import ArchitectRole, SecurityRole; print('OK')"`

**Task X2: Create the council orchestrator in src/council/council.py**

Claude Code prompt:
```
Create src/council/council.py.
- Council class running multi-agent deliberation
- deliberate(question, mode='full') with stages:
  1. LEAD decomposes the question
  2. ARCHITECT and SECURITY answer independently (sequential on M5 Pro)
  3. DEVIL'S ADVOCATE reviews both and challenges them
  4. REVIEWER synthesises into final recommendation + rationale
  5. Returns: {question, architect_view, security_view, challenges,
     final_recommendation, rationale, models_used, timings}
- Show progress per agent (which role is thinking now)
- Reuse Phase 3 Orchestrator patterns; sequential model loading (quality-first)
- Log full deliberation to memory AND offer to write to Obsidian
- modes: 'full' (all roles), 'quick' (architect + reviewer), 'debate'
  (architect vs devil's advocate + judge)
```

Verification:
```bash
python3 -c "from src.council.council import Council; print('Council ready')"
```

**Task X3: Wire `axiom council` command + Obsidian write**

Claude Code prompt:
```
Update axiom.py to add a 'council' subcommand:
  axiom council "question"                 -> full deliberation
  axiom council "question" --mode quick    -> architect + reviewer
  axiom council "question" --mode debate   -> architect vs devil's advocate
After deliberation, ask: "Write this decision to Obsidian? (yes/no)"
If yes, use ObsidianVault.write_decision() to save a linked decision note.
Print the final recommendation with rich formatting. Keep all existing commands working.
```

Verification:
```bash
python3 axiom.py council "Should this bank use OCSP stapling or short-lived certificates for TLS?" --mode quick
```

**Task X4: Add GLM-5.2 cloud escalation to the council**

Claude Code prompt:
```
Add GLM-5.2 cloud escalation to src/council/council.py.
- Add a ComplexityScorer (reuse the CLM-OS token-optimiser approach):
  scores a sub-question 0-100 on reasoning depth, length, ambiguity, and
  number of competing considerations
- In the council, the REVIEWER step checks the score:
    score > 60 OR user passed --complex  ->  model = "glm-5.2:cloud"
    otherwise                            ->  local model (qwen3:30b)
- glm-5.2:cloud is called through the SAME OllamaClient — just a model name string
- Add config/council.yaml keys:
    cloud:
      enabled: true
      model: "glm-5.2:cloud"
      complexity_threshold: 60
      tier: "free"
- If the cloud call fails (no SLA), fall back to local qwen3:30b automatically
  and note the degradation in the output
- Add --complex flag to `axiom council` to force cloud escalation
- Log whether each council ran local or cloud, for cost visibility
```

Verification:
```bash
ollama login
ollama run glm-5.2:cloud "Confirm you are GLM-5.2 and your context window size"
python3 axiom.py council "Design a crypto-agile PKI migration strategy for a national bank facing PQC mandates, balancing HSM constraints, CA hierarchy redesign, and zero-downtime rollover" --complex
# PASS if: reviewer routes to glm-5.2:cloud, returns frontier synthesis, logs cloud use
```

---

## BLOCK Y — Voice-Enabled Interactive UI

**Task Y1: Upgrade the web UI with voice + council + Obsidian**

Claude Code prompt:
```
Upgrade src/interface/web/ (the Phase 2 FastAPI app):
- Add a microphone button that records audio in the browser (MediaRecorder),
  sends it to a new POST /voice endpoint
- POST /voice: receives audio, runs SpeechToText (whisper), routes the
  transcribed text, returns the response
- Add a "Speak responses" toggle: when on, response goes to TTS (Voxtral) and
  audio plays in the browser
- Add a mode selector: Single / Ensemble / Council
- Add an Obsidian panel: show recent vault notes + a "save to vault" button on
  any AXIOM response
- Clean, dark-themed, professional (match AXIOM branding). All processing local.
```

Verification:
```bash
python3 server.py
# Browser: mic records + transcribes + responds; speak toggle plays audio;
# council mode runs multi-agent flow; save-to-vault writes a note
```

**Task Y2: Add `axiom serve` as the primary launch command**

Claude Code prompt:
```
Update axiom.py / server.py so `axiom serve` launches the full voice-enabled
web UI with council and Obsidian integration. Print the AXIOM banner and URL.
Confirm Ollama, whisper, and the vault path are available before starting.
```

Verification: `python3 axiom.py serve` launches the full UI.

---

## BLOCK Z — Docs + Git

**Task Z1: Update README.md + JOURNAL.md**
- Document the council (multi-agent) architecture + role table
- Document Obsidian two-way integration (vault path setup)
- Document GLM-5.2 cloud escalation (free-tier posture, complexity routing, SLA caveat)
- Document the voice-enabled web UI
- Update roadmap: Phase 5 complete
- Council architecture diagram

**Task Z2: Update .gitignore**
```
# Vault is personal knowledge — lives outside the repo (~/Obsidian/AXIOM-Brain)
# Never commit vault contents
```

**Task Z3: Commit, merge, tag v0.5.0**
```bash
cd ~/AI-Projects/axiom
git add .
git commit -m "feat: AXIOM v0.5.0 — multi-agent council + Obsidian brain + voice UI + GLM-5.2 cloud

- Multi-agent council: architect, security, devil's advocate, reviewer roles
- Agents question and challenge each other; reviewer synthesises
- Obsidian two-way integration: reads vault for context, writes decisions back
- GLM-5.2 cloud escalation via Ollama Cloud (complexity-gated, free-tier, local fallback)
- Voice-enabled interactive web UI (mic in, Voxtral out)
- Council/ensemble/single modes selectable in UI
- Vault semantic index (axiom_vault collection)
"
git checkout main && git merge phase-5-council
git tag v0.5.0
git push origin main --tags
git branch -d phase-5-council
```

---

## Phase 5 Success Criteria

```bash
# 1. Obsidian write
python3 -c "from src.brain.vault import ObsidianVault; ObsidianVault().write_note('concepts','Test','content',tags=['t'])"
# PASS if: note appears in vault, opens correctly in Obsidian

# 2. Obsidian read + search
python3 axiom.py "what did I note about OCSP last week"
# PASS if: AXIOM retrieves relevant vault notes

# 3. Council — full deliberation
python3 axiom.py council "OCSP stapling vs short-lived certs for a bank"
# PASS if: architect, security, devil's advocate weigh in; reviewer synthesises;
#          offers to write decision to Obsidian

# 4. Council writes decision to vault (answer 'yes' to the write prompt)
# PASS if: a structured decision note appears in vault/decisions/

# 5. GLM-5.2 cloud escalation
python3 axiom.py council "Design a crypto-agile PQC migration for a national bank" --complex
# PASS if: routes to glm-5.2:cloud, returns frontier synthesis, logs cloud use;
#          if cloud down, degrades to local qwen3:30b with a note

# 6. Voice web UI
python3 axiom.py serve
# PASS if: mic records + transcribes; speak toggle plays TTS; council mode works;
#          save-to-vault works

# 7. Regression — all prior phases
python3 axiom.py "draft an email"               # CLI
python3 axiom.py voice                           # voice loop
python3 axiom.py "analyse RFP" --mode ensemble   # orchestration
# PASS if: all still function

# 8. GitHub
# PASS if: v0.5.0 tagged and pushed
```

---

## Execution Order

```
0.1 -> 0.4                       # Branch + vault folder + cloud check + watchdog
W1 -> W2                        # Obsidian brain (read/write + index)
X1 -> X2 -> X3 -> X4            # Council: roles -> orchestrator -> command -> cloud escalation
Y1 -> Y2                        # Voice web UI
Z1 -> Z2 -> Z3                  # Docs + merge
```

Total tasks: 14
Estimated: 1-2 focused sessions (council testing is slow — many sequential
model loads per deliberation; quality-first tradeoff as established).

X4 (cloud) comes AFTER X3 (local council working) so you validate the local
council before layering the cloud path on top.

---

## Build Notes for Claude Code

- Obsidian needs NO API or plugin — AXIOM reads/writes plain .md files; Obsidian
  picks up changes live
- The vault is personal knowledge — keep it OUTSIDE the git repo, never commit it
- Council deliberation is SEQUENTIAL on M5 Pro (one model at a time) — a full
  4-role council could take 5-10 minutes. Show per-role progress. Offer 'quick'
  mode (2 roles) for faster turns.
- glm-5.2:cloud is a model-name string through the SAME ollama client — confirm
  `ollama login` first. Always provide a local fallback if cloud fails.
- Tag every AXIOM-written vault claim with provenance (extracted/inferred/decision)
- Reuse Phase 3 Orchestrator and Phase 4 voice components — don't rebuild
- Default council models: lead/devil/reviewer = qwen3:30b, architect = qwen3.6:27b,
  security = deepseek-r1:32b (configurable in council.yaml)
