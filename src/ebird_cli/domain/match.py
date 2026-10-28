"""Finding text in what an observation shows, ignoring case and accents."""

import unicodedata


def fold(text: str) -> str:
    """Text without case or accents, so that "Héron" and "heron" compare equal."""
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(char for char in decomposed if not unicodedata.combining(char)).casefold()


def contains(value: str, text: str) -> bool:
    return fold(text) in fold(value)


def spans(value: str, text: str) -> list[tuple[int, int]]:
    """The start and end, in value, of each occurrence of text, so the accented letters shown can be highlighted."""
    wanted = fold(text)
    if not wanted:
        return []
    folded = ""
    origins = []
    for index, char in enumerate(value):
        folded_char = fold(char)
        folded += folded_char
        origins += [index] * len(folded_char)
    found = []
    start = folded.find(wanted)
    while start != -1:
        end = start + len(wanted)
        found.append((origins[start], origins[end - 1] + 1))
        start = folded.find(wanted, end)
    return found
