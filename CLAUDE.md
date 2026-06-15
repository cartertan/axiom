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
