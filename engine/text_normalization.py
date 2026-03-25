import re
import unicodedata

# Best efforts normalization map for visual obfuscation
CHAR_SUBS = {
    "0": "o",
    "1": "l",
    "3": "e",
    "4": "a",
    "5": "s",
    "7": "t",
    "@": "a",
    "$": "s",
    "!": "i",
}

LINK_PATTERN = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
WORD_SPLIT = re.compile(r"[^\w]+")


def normalize_text(text: str) -> str:
    if not text:
        return ""

    norm = unicodedata.normalize("NFKC", text)
    norm = norm.strip().lower()

    out = []
    for char in norm:
        out.append(CHAR_SUBS.get(char, char))
    norm = "".join(out)

    norm = re.sub(r"\s+", " ", norm)
    norm = norm.replace("[dot]", ".").replace("(dot)", ".")

    return norm


def extract_signals(text: str) -> dict:
    normalized = normalize_text(text)
    signals = {
        "has_link": bool(LINK_PATTERN.search(normalized)),
        "has_mention": "@" in normalized,
        "word_count": len(WORD_SPLIT.split(normalized)),
        "raw": text,
        "normalized": normalized,
    }
    return signals


def text_distance(a: str, b: str) -> float:
    return 1.0 if a == b else 0.0
