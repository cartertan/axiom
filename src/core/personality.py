import yaml


class PersonalityLayer:
    def __init__(self):
        self._config: dict | None = None

    def load_config(self, path: str = "config/personality.yaml") -> dict:
        """Load and cache the AXIOM personality config from YAML. Returns the config dict."""
        if self._config is None:
            try:
                with open(path) as f:
                    self._config = yaml.safe_load(f)
            except FileNotFoundError:
                raise FileNotFoundError(
                    f"Personality config not found at {path}. Ensure config/personality.yaml exists."
                )
        return self._config

    def get_personality_prompt(self) -> str:
        """Return a formatted string block describing AXIOM's identity, character,
        forbidden phrases, and rules for injection into an agent's system prompt."""
        c = self.load_config()
        character = "\n".join(f"- {trait}" for trait in c.get("character", []))
        forbidden = ", ".join(f'"{p}"' for p in c.get("forbidden_phrases", []))
        rules = "\n".join(f"- {rule}" for rule in c.get("rules", []))
        return (
            f"You are {c['identity']}.\n\n"
            f"Character:\n{character}\n\n"
            f"Never use these phrases or their equivalents: {forbidden}.\n\n"
            f"Rules:\n{rules}"
        )
