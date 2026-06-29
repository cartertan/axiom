"""
AXIOM Obsidian Integration
Two-way vault access: write structured notes, search existing content.
Vault lives at ~/Obsidian/AXIOM-Brain/ — outside the repo, never committed.
"""

import os
import glob
from datetime import datetime
from pathlib import Path


# Load vault path from env or use default
VAULT_PATH = Path(os.getenv("OBSIDIAN_VAULT_PATH", "~/Obsidian/AXIOM-Brain")).expanduser()

VALID_FOLDERS = ["decisions", "summaries", "research", "pki"]


def _ensure_vault():
    """Confirm vault path exists. Warn but do not crash if missing."""
    if not VAULT_PATH.exists():
        print(f"[OBSIDIAN WARNING] Vault not found at {VAULT_PATH}")
        print("Run: mkdir -p ~/Obsidian/AXIOM-Brain/{decisions,summaries,research,pki}")
        return False
    return True


def write_note(
    folder: str,
    title: str,
    content: str,
    tags: list = None,
    provenance: str = "decision",
    model: str = "axiom"
) -> str:
    """
    Write a structured Markdown note to the Obsidian vault.

    Args:
        folder:     Target subfolder — decisions, summaries, research, pki
        title:      Note title (used as filename)
        content:    Main body content
        tags:       List of tags e.g. ["pki", "council"]
        provenance: extracted | inferred | decision
        model:      Which model produced the content

    Returns:
        Full path to written file, or error string
    """
    if not _ensure_vault():
        return "ERROR: vault not found"

    if folder not in VALID_FOLDERS:
        folder = "summaries"

    # Build frontmatter
    timestamp = datetime.now().isoformat(timespec="seconds")
    tag_list = tags or ["axiom"]
    tag_str = ", ".join(f'"{t}"' for t in tag_list)

    frontmatter = f"""---
date: {timestamp}
tags: [{tag_str}]
provenance: {provenance}
model: {model}
---

"""

    # Sanitise title for filename
    safe_title = title.replace(" ", "-").replace("/", "-").replace(":", "")[:80]
    date_prefix = datetime.now().strftime("%Y-%m-%d")
    filename = f"{date_prefix}-{safe_title}.md"

    target_dir = VAULT_PATH / folder
    target_dir.mkdir(parents=True, exist_ok=True)
    filepath = target_dir / filename

    full_content = frontmatter + f"# {title}\n\n{content}"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(full_content)

    print(f"[OBSIDIAN] Written: {filepath}")
    return str(filepath)


def search_vault(query: str, max_results: int = 3) -> list:
    """
    Search vault for notes containing query terms.
    Returns list of dicts with title, folder, snippet, path.

    Simple grep-based search — no embeddings needed.
    """
    if not _ensure_vault():
        return []

    results = []
    query_lower = query.lower()
    terms = query_lower.split()

    # Search all .md files in vault
    pattern = str(VAULT_PATH / "**" / "*.md")
    all_files = glob.glob(pattern, recursive=True)

    for filepath in all_files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            content_lower = content.lower()

            # Score by how many terms match
            score = sum(1 for term in terms if term in content_lower)
            if score == 0:
                continue

            # Extract a relevant snippet (first matching paragraph)
            lines = content.split("\n")
            snippet_lines = []
            for line in lines:
                if any(term in line.lower() for term in terms):
                    snippet_lines.append(line.strip())
                if len(snippet_lines) >= 3:
                    break

            snippet = " ".join(snippet_lines)[:300]
            folder = Path(filepath).parent.name

            results.append({
                "title": Path(filepath).stem,
                "folder": folder,
                "snippet": snippet,
                "path": filepath,
                "score": score
            })

        except Exception as e:
            continue

    # Sort by score descending, return top results
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:max_results]


def get_vault_context(query: str) -> str:
    """
    Returns a formatted string of vault context for injection into prompts.
    Used by council orchestrator before every deliberation.
    """
    results = search_vault(query, max_results=2)

    if not results:
        return ""

    context_parts = ["[VAULT CONTEXT — from your Obsidian brain]"]
    for r in results:
        context_parts.append(f"\n### {r['title']} ({r['folder']})")
        context_parts.append(r["snippet"])

    return "\n".join(context_parts)


def list_recent_notes(folder: str = None, limit: int = 5) -> list:
    """
    Return most recently modified notes, optionally filtered by folder.
    Used by web UI vault panel.
    """
    if not _ensure_vault():
        return []

    if folder:
        pattern = str(VAULT_PATH / folder / "*.md")
    else:
        pattern = str(VAULT_PATH / "**" / "*.md")

    files = glob.glob(pattern, recursive=True)

    # Sort by modification time descending
    files.sort(key=lambda x: os.path.getmtime(x), reverse=True)

    results = []
    for filepath in files[:limit]:
        results.append({
            "title": Path(filepath).stem,
            "folder": Path(filepath).parent.name,
            "modified": datetime.fromtimestamp(
                os.path.getmtime(filepath)
            ).strftime("%Y-%m-%d %H:%M"),
            "path": filepath
        })

    return results
