import re

_MAX_SPOKEN_CHARS = 1200

_MARKDOWN_FENCES = re.compile(r"```[\s\S]*?```")
_INLINE_CODE = re.compile(r"`[^`]+`")
_BOLD_ITALIC = re.compile(r"\*{1,3}(.*?)\*{1,3}")
_HEADERS = re.compile(r"^#{1,6}\s+", re.MULTILINE)
_URLS = re.compile(r"https?://\S+")
_BULLET = re.compile(r"^\s*[-*•]\s+", re.MULTILINE)
_NUMBERED = re.compile(r"^\s*\d+\.\s+", re.MULTILINE)
_WHITESPACE = re.compile(r"\s+")

_ORDINALS = ["First", "Second", "Third", "Fourth", "Fifth",
             "Sixth", "Seventh", "Eighth", "Ninth", "Tenth"]

_ABBREVS = {
    "e.g.": "for example",
    "i.e.": "that is",
    "etc.": "and so on",
    "vs.": "versus",
    "approx.": "approximately",
    "Fig.": "Figure",
    "fig.": "figure",
}


def _convert_numbered_list(text: str) -> str:
    lines = text.splitlines()
    ordinal_index = 0
    result = []
    for line in lines:
        m = _NUMBERED.match(line)
        if m:
            label = _ORDINALS[ordinal_index] if ordinal_index < len(_ORDINALS) else f"Item {ordinal_index + 1}"
            result.append(label + ", " + line[m.end():])
            ordinal_index += 1
        else:
            if not _NUMBERED.match(line):
                ordinal_index = 0
            result.append(line)
    return "\n".join(result)


def clean_for_speech(text: str) -> str:
    """Strip markdown and prepare text for natural spoken delivery."""
    for abbr, expansion in _ABBREVS.items():
        text = text.replace(abbr, expansion)

    text = _MARKDOWN_FENCES.sub(" ", text)
    text = _INLINE_CODE.sub(lambda m: m.group(0)[1:-1], text)
    text = _convert_numbered_list(text)
    text = _BULLET.sub("", text)
    text = _BOLD_ITALIC.sub(r"\1", text)
    text = _HEADERS.sub("", text)
    text = _URLS.sub("link", text)

    text = text.replace("#", "").replace(">", "")

    text = _WHITESPACE.sub(" ", text).strip()

    if len(text) > _MAX_SPOKEN_CHARS:
        cutoff = text.rfind(". ", 0, _MAX_SPOKEN_CHARS)
        if cutoff == -1:
            cutoff = _MAX_SPOKEN_CHARS
        text = text[:cutoff + 1] + " — full response is shown in text above."

    return text
