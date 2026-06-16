# AXIOM — Model Stack Analysis & Recommendations
**Date:** 2026-06-15 (Updated: upgrades confirmed complete)
**Hardware:** MacBook Pro M5 Pro, 64GB Unified RAM
**Status:** ✅ Stack upgrade complete

---

## Confirmed Active Stack (Post-Upgrade)

| Model | Role | Status |
|---|---|---|
| `qwen3:30b` | Primary reasoning + RFP analysis | ✅ NEW — replaces QwQ |
| `qwen3.6:27b` | Primary writer — email, proposals, PKI Q&A | ✅ Promoted |
| `granite4.1:30b` | Structured output, RAG, compliance matrices | ✅ Retained |
| `deepseek-r1:32b` | Deep research, chain-of-thought analysis | ✅ Retained |
| `gemma4:e4b` | Task router, tool calling, vision, fast tasks | ✅ Upgraded role |
| `devstral-small-2` | Agentic coding — multi-file edits, debugging | ✅ NEW — replaces devstral:latest |
| `nomic-embed-text` | RAG embeddings | ✅ Retained |

**Retired:**
- ~~`qwq:latest`~~ — superseded by qwen3:30b
- ~~`devstral:latest`~~ — superseded by devstral-small-2

---

## Model Roles & Reasoning

### 1. `qwen3:30b` — Primary Reasoning Engine
**Replaces:** `qwq:latest`

QwQ was Qwen's standalone reasoning model (late 2024). Qwen3 fully supersedes it:
- Outperforms QwQ-32B on reasoning, math, and coding
- Built-in thinking mode toggle (ON for deep analysis, OFF for speed)
- Better instruction following and multi-turn dialogue
- QwQ could only think — Qwen3 does both thinking and non-thinking in one model

**Jarvis tasks:**
- RFP analysis (thinking mode ON)
- Logical gap analysis in customer requirements
- Assumption validation
- Any task requiring structured step-by-step reasoning

---

### 2. `qwen3.6:27b` — Primary Writing Model
**Promoted from:** Proposal writing only → now primary customer-facing writer

The Qwen3 family leads on human preference alignment — creative writing,
multi-turn dialogue, instruction following across 119 languages.
Outperforms granite4.1 on tone, nuance, and conversational quality.

**Jarvis tasks:**
- Email drafting (customer-facing)
- Proposal narrative sections
- PKI Q&A (technical explanations in natural language)
- Any output Carter sends to a customer or prospect

---

### 3. `granite4.1:30b` — Structured Output Specialist
**Role:** Retained and focused

IBM's enterprise model trained specifically for:
- Reliable JSON/structured output
- Native RAG integration
- Tool calling with function schemas
- 512K context window — handles very long documents

**Jarvis tasks:**
- Meeting summaries (structured format with sections)
- Compliance matrices (Excel-ready output)
- JSON responses for agent tool calls
- Document chunking and extraction tasks

**Note:** Not the strongest writer. Do not use for customer-facing prose.

---

### 4. `deepseek-r1:32b` — Deep Reasoning & Research
**Role:** Retained as analytical engine

DeepSeek R1's chain-of-thought distillation gives it unique capability
for multi-step decomposition. The R1-0528 update (May 2025) reduced
hallucinations by ~45% and improved accuracy significantly.
32B is the safe ceiling on this machine — 70B crashes when other apps are open.

**Jarvis tasks:**
- Competitive intelligence research
- Risk identification in RFPs
- Multi-source synthesis (research agent)
- Any task needing "think step by step through this problem"

---

### 5. `gemma4:e4b` — Agent Router & Tool Caller
**Role:** Upgraded from "fast fallback" to active orchestration layer

Google's 4B MoE model (only ~4B active params). Released April 2026.
The consensus best-in-class model for tool calling and function dispatch.
Native vision support — can process screenshots and diagrams.
Runs in ~6GB RAM — the "always-on" lightweight layer.

**Jarvis tasks:**
- Intent classification (what task type is this?)
- Agent dispatch (which agent + model handles this?)
- Tool function calls and response parsing
- Vision input (screenshots, diagrams, uploaded images)
- Sub-5-second responses for quick questions

---

### 6. `devstral-small-2` — Agentic Coding Specialist
**Replaces:** `devstral:latest`

Devstral Small 2 (December 2025) — 68% SWE-bench Verified.
Built specifically for agentic coding loops: multi-file edits, codebase navigation,
debugging, function calling. Added vision capabilities vs the original.
On the M5 Pro 64GB, can run at Q5_K_M or Q8 quality — higher than most hardware allows.

**Jarvis tasks:**
- Building Jarvis itself (used via Claude Code)
- Code review and debugging
- Multi-file refactoring
- Generating scripts and automation tools

---

### 7. `nomic-embed-text` — RAG Embeddings
**Role:** Unchanged

Still the standard for Ollama-native semantic embeddings.
Proven working in presales-ai-platform (287 chunks, 11 products, 10 verticals).
No reason to change — consistency with existing RAG pipeline is more valuable
than marginal gains from switching embedding models.

---

## Task → Model Assignment (Final)

| Task | Primary Model | Fallback | Why |
|---|---|---|---|
| Email drafting | `qwen3.6:27b` | `granite4.1:30b` | Best tone and human preference alignment |
| Meeting summary | `granite4.1:30b` | `qwen3.6:27b` | Reliable structured sections + JSON |
| RFP analysis | `qwen3:30b` | `deepseek-r1:32b` | Thinking mode ON, structured reasoning |
| PKI Q&A (RAG) | `qwen3.6:27b` | `granite4.1:30b` | Natural technical explanation |
| Research / intel | `deepseek-r1:32b` | `qwen3:30b` | Chain-of-thought synthesis |
| Task routing | `gemma4:e4b` | — | Sub-second intent classification |
| Tool calling | `gemma4:e4b` | `granite4.1:30b` | Best function dispatch at any size |
| Vision input | `gemma4:e4b` | — | Only vision-capable model in stack |
| Fast / general | `gemma4:e4b` | `granite4.1:30b` | 6GB load, ~3 sec response |
| Agentic coding | `devstral-small-2` | `qwen3.6:27b` | Purpose-built for code agent loops |
| Benchmarking | All models | — | That is the point |
| RAG embeddings | `nomic-embed-text` | — | Consistent with presales-ai-platform |

---

## Benchmark Priority Order (Phase 3)

When the Jarvis benchmark engine runs, compare models in this order
across each task type to generate the most useful report:

```
Tier 1 (primary candidates):   qwen3.6:27b    qwen3:30b      deepseek-r1:32b
Tier 2 (structured specialists): granite4.1:30b
Tier 3 (speed reference):        gemma4:e4b
Tier 4 (coding reference):       devstral-small-2
```

Benchmark scoring formula:
  Score = (quality_rating × 0.6) + (speed_score × 0.25) + (token_efficiency × 0.15)

---

## Why This Stack Is Portfolio-Worthy

Five different model families running head-to-head on real presales tasks:
- IBM (granite4.1) — enterprise structured output
- Alibaba (qwen3 family) — reasoning + writing
- Google (gemma4) — agent orchestration + vision
- Mistral (devstral-small-2) — agentic coding
- DeepSeek (deepseek-r1) — chain-of-thought research

No one else has this exact multi-vendor comparison on presales tasks published.
The Phase 3 benchmark report becomes a LinkedIn article and a GitHub asset.

