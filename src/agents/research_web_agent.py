from src.actions.web_search import WebSearch
from src.agents.base_agent import BaseAgent

_TASK_DESCRIPTION = (
    "You are a research analyst. You have been given a question and a set of web sources. "
    "Your job is to synthesise the sources into a clear, well-structured research brief.\n"
    "Rules:\n"
    "- Cite sources inline using [Source N] notation.\n"
    "- Clearly distinguish confirmed facts (from sources) from your interpretation.\n"
    "- Flag any conflicting information across sources.\n"
    "- End with a 'Sources' section listing each URL.\n"
    "- Be concise — a tight 300-600 word brief beats a sprawling essay."
)


class ResearchWebAgent(BaseAgent):
    def __init__(self, config, profile, memory, ollama_client):
        super().__init__(config, profile, memory, ollama_client)
        self._web = WebSearch()

    def run(self, user_input: str, task_type: str = "RESEARCH") -> str:
        model = self.config["task_models"]["research"]["primary"]
        print(f"  Searching: {user_input[:80]}...")

        results = self._web.search(user_input, max_results=5)
        if not results:
            return "No web results found for that query."

        print(f"  Found {len(results)} results. Fetching top pages...")
        sources_text = ""
        for i, r in enumerate(results[:3], start=1):
            print(f"  Fetching [{i}] {r['url'][:70]}...")
            page_text = self._web.fetch_page(r["url"])
            sources_text += (
                f"\n[Source {i}] {r['title']}\nURL: {r['url']}\n"
                f"Snippet: {r['snippet']}\nContent:\n{page_text[:2000]}\n\n"
            )

        # Also include snippets for results 4-5 (not full pages)
        for i, r in enumerate(results[3:], start=4):
            sources_text += f"\n[Source {i}] {r['title']}\nURL: {r['url']}\nSnippet: {r['snippet']}\n"

        system_prompt = self.build_system_prompt(_TASK_DESCRIPTION)
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    f"Research question: {user_input}\n\n"
                    f"Web sources:\n{sources_text}\n\n"
                    f"Synthesise these sources into a research brief."
                ),
            },
        ]

        print(f"  Synthesising with {model}...")
        response = self.ollama.chat(model, messages)
        self.log_to_memory(task_type, user_input, response, model)
        return response
