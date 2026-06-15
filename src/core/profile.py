import json


class ProfileLoader:
    def __init__(self):
        self._profile: dict | None = None

    def load_profile(self, path: str = "memory/carter_profile.json") -> dict:
        """Load and cache the Carter profile from JSON. Returns the profile dict."""
        if self._profile is None:
            try:
                with open(path) as f:
                    self._profile = json.load(f)
            except FileNotFoundError:
                raise FileNotFoundError(
                    f"Profile not found at {path}. Ensure memory/carter_profile.json exists."
                )
        return self._profile

    def format_for_prompt(self) -> str:
        """Return a concise multi-line profile summary for injection into LLM system prompts."""
        p = self.load_profile()
        expertise = ", ".join(p.get("expertise", []))
        customers = ", ".join(p.get("typical_customers", []))
        products = ", ".join(p.get("products", []))
        return (
            f"You are assisting {p['name']}, {p['role']} at {p['company']} in {p['location']}.\n"
            f"Experience: {p.get('years_experience', '')} years in cybersecurity and enterprise IT.\n"
            f"Core expertise: {expertise}.\n"
            f"Typical customers: {customers} — titles include {', '.join(p.get('customer_titles', []))}.\n"
            f"Products: {products}.\n"
            f"Communication style: {p.get('communication_style', '')}.\n"
            f"Preferred tone: {p.get('preferred_tone', '')}.\n"
            f"Preferred format: {p.get('preferred_format', '')}.\n"
            f"Always write as if you are {p['name']} or directly supporting him."
        )
