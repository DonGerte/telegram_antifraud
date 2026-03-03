"""Honeypot templates and similarity detection for spam classification.

Uses simple edit distance (Levenshtein) to group similar spam messages.
Maintains a database of known spam templates.
"""
import re
from collections import defaultdict

# Base keywords for quick detection
KEYWORDS = [r"zapato", r"bolsa", r"oferta", r"descuento", r"envío", r"gratis", 
            r"promo", r"venta", r"compra", r"precio", r"whatsapp", r"contactar"]
LINK_PATTERN = re.compile(r"https?://")

# Template database: category -> [patterns]
SPAM_TEMPLATES = defaultdict(list)


def levenshtein(s1, s2):
    """Simple edit distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein(s2, s1)
    if len(s2) == 0:
        return len(s1)
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]


def similarity(s1, s2, threshold=0.8):
    """Return True if strings are similar above threshold (0-1)."""
    if not s1 or not s2:
        return False
    max_len = max(len(s1), len(s2))
    if max_len == 0:
        return True
    dist = levenshtein(s1.lower(), s2.lower())
    sim = 1.0 - (dist / max_len)
    return sim >= threshold


def check_honeypot(text: str) -> bool:
    """Check if text matches spam patterns (links, keywords, templates)."""
    if not text:
        return False
    
    # Quick link check
    if LINK_PATTERN.search(text):
        return True
    
    # Keyword matching
    for kw in KEYWORDS:
        if re.search(kw, text, re.IGNORECASE):
            return True
    
    # Template similarity check
    for category in SPAM_TEMPLATES:
        for template in SPAM_TEMPLATES[category]:
            if similarity(text, template, threshold=0.75):
                return True
    
    return False


def register_template(category: str, text: str):
    """Register a spam text as a template for future detection."""
    if text not in SPAM_TEMPLATES[category]:
        SPAM_TEMPLATES[category].append(text)


def get_templates(category: str = None):
    """Get all templates or those from a specific category."""
    if category:
        return SPAM_TEMPLATES.get(category, [])
    return dict(SPAM_TEMPLATES)


# Pre-load some common templates
_common = ["offers on shoes", "get free shipping", "click here to buy", 
           "limited time sale", "contact for details"]
for tmpl in _common:
    register_template("spam", tmpl)
