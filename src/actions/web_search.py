import re

import requests
from bs4 import BeautifulSoup

try:
    from ddgs import DDGS  # ddgs >= 9.x (renamed from duckduckgo_search)
except ImportError:
    from duckduckgo_search import DDGS  # legacy fallback

# Search backend is pluggable via config (see config/models.yaml web_search.backend).
# Default: DuckDuckGo — free, no API key required.
# Future alternatives: brave, searxng (swap in _build_backend).


class WebSearch:
    def __init__(self, backend: str = "duckduckgo", max_fetch_words: int = 3000):
        self._backend = backend
        self._max_words = max_fetch_words

    def search(self, query: str, max_results: int = 5) -> list[dict]:
        """Return list of {title, url, snippet} from the configured backend."""
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", ""),
                })
        return results

    def fetch_page(self, url: str) -> str:
        """Fetch a URL and return cleaned readable text, capped at max_fetch_words words."""
        try:
            resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
        except Exception as e:
            return f"[Could not fetch {url}: {e}]"

        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)
        text = re.sub(r"\s{2,}", " ", text)
        words = text.split()
        if len(words) > self._max_words:
            words = words[: self._max_words]
        return " ".join(words)
