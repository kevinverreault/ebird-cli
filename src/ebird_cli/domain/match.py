"""Finding text in what an observation shows, ignoring case and accents."""

import unicodedata


def fold(text: str) -> str:
    """Text without case or accents, so that "Héron" and "heron" compare equal."""
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(char for char in decomposed if not unicodedata.combining(char)).casefold()


def contains(value: str, text: str) -> bool:
    return fold(text) in fold(value)
