"""The command-line grammar of a command: the words it accepts after its name, and what to offer while they're typed."""

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

from prompt_toolkit.completion import Completion

FLAG_PREFIX = "-"

Arguments = dict[str, str | None]


class CommandLineError(Exception):
    """A line that the command's grammar does not accept."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


@dataclass(frozen=True)
class Positional:
    """A mandatory word, before any flag, that must be one of choices."""

    name: str
    choices: Sequence[str]


@dataclass(frozen=True)
class Flag:
    """An optional -name followed by its value: one word, or every word up to the next flag when multi_word.

    A value outside choices falls back to default. suggestions(typed, arguments) gives the completions for what was
    typed after the flag; without it, completion offers the choices containing it. The flag isn't offered while
    hidden_when(positional arguments) holds.
    """

    name: str
    multi_word: bool = False
    default: str | None = None
    choices: Sequence[str] | None = None
    suggestions: Callable[[str, Arguments], list[str]] | None = None
    hidden_when: Callable[[Arguments], bool] = lambda _arguments: False

    def accepts(self, value: str) -> bool:
        return self.choices is None or value in self.choices

    def complete(self, typed: str, arguments: Arguments) -> list[str]:
        if self.suggestions is not None:
            return self.suggestions(typed, arguments)
        return [choice for choice in self.choices or [] if typed in choice]

    @property
    def token(self) -> str:
        return f"{FLAG_PREFIX}{self.name}"


class Grammar:
    """The words a command accepts after its name."""

    def __init__(self, positionals: Sequence[Positional], flags: Sequence[Flag]):
        self.positionals = tuple(positionals)
        self.flags = tuple(flags)

    def parse(self, words: list[str]) -> Arguments:
        """The value of each argument named in the line, or CommandLineError when the grammar does not accept it."""
        reading = self._read(words)
        for flag in self.flags:
            if reading.flag_words.get(flag.name) == []:
                raise CommandLineError(f"argument {flag.token}: expected one argument")
        for positional, word in self._typed_positionals(reading):
            if word not in positional.choices:
                choices = ", ".join(repr(choice) for choice in positional.choices)
                raise CommandLineError(f"argument {positional.name}: invalid choice: {word!r} (choose from {choices})")
        missing = [positional.name for positional in self.positionals[len(reading.positional_words) :]]
        if missing:
            raise CommandLineError(f"the following arguments are required: {', '.join(missing)}")
        unrecognized = reading.positional_words[len(self.positionals) :] + reading.unrecognized
        if unrecognized:
            raise CommandLineError(f"unrecognized arguments: {' '.join(unrecognized)}")

        arguments = self._positional_arguments(reading)
        for flag in self.flags:
            values = reading.flag_words.get(flag.name)
            value = " ".join(values) if values else None
            arguments[flag.name] = value if value is not None and flag.accepts(value) else flag.default
        return arguments

    def complete(self, text: str) -> list[Completion]:
        """What to offer for the word being typed at the end of text, the words after the command name."""
        *words, typed = text.split(" ")
        words = [word for word in words if word]
        reading = self._read(words)
        if reading.flag is None and len(reading.positional_words) < len(self.positionals):
            choices = self.positionals[len(reading.positional_words)].choices
            return [
                Completion(choice, start_position=-len(typed))
                for choice in choices
                if choice.lower().startswith(typed.lower())
            ]
        if typed.startswith(FLAG_PREFIX) or (typed == "" and not reading.takes_another_word()):
            positional_arguments = self._positional_arguments(reading)
            return [
                Completion(flag.token, start_position=-len(typed))
                for flag in self.flags
                if flag.name not in reading.flag_words
                and not flag.hidden_when(positional_arguments)
                and typed.lower() in flag.token.lower()
            ]
        if not reading.takes_another_word():
            return []
        try:
            arguments = self.parse([*words, typed])
        except CommandLineError:
            return []
        flag = reading.flag
        typed_value = " ".join([*reading.flag_words[flag.name], typed])
        return [Completion(value, start_position=-len(typed_value)) for value in flag.complete(typed_value, arguments)]

    def _typed_positionals(self, reading: "_Reading") -> list[tuple[Positional, str]]:
        """Each positional with the word typed for it, for as many as the line has."""
        return list(zip(self.positionals, reading.positional_words, strict=False))

    def _positional_arguments(self, reading: "_Reading") -> Arguments:
        return {positional.name: word for positional, word in self._typed_positionals(reading)}

    def _flag(self, word: str) -> Flag | None:
        """The flag a word names: exactly, or as a prefix of only that flag."""
        matches = [flag for flag in self.flags if flag.token == word] or [
            flag for flag in self.flags if flag.token.startswith(word)
        ]
        return matches[0] if len(matches) == 1 else None

    def _read(self, words: list[str]) -> "_Reading":
        reading = _Reading()
        for word in words:
            if is_flag_token(word):
                reading.flag = self._flag(word)
                if reading.flag is None:
                    reading.unrecognized.append(word)
                else:
                    reading.flag_words[reading.flag.name] = []
            elif reading.takes_another_word():
                reading.flag_words[reading.flag.name].append(word)
            elif reading.flag is None and not reading.unrecognized and not reading.flag_words:
                reading.positional_words.append(word)
            else:
                reading.unrecognized.append(word)
        return reading


def is_flag_token(word: str) -> bool:
    """Whether a word names a flag; a dash before a digit, as in -3, is a value."""
    return word.startswith(FLAG_PREFIX) and word[len(FLAG_PREFIX) : len(FLAG_PREFIX) + 1].isalpha()


@dataclass
class _Reading:
    """The words of a line sorted into positionals, the values of each flag, and words no argument takes."""

    positional_words: list[str] = field(default_factory=list)
    flag_words: dict[str, list[str]] = field(default_factory=dict)
    unrecognized: list[str] = field(default_factory=list)
    flag: Flag | None = None

    def takes_another_word(self) -> bool:
        """Whether the flag being read would take the next word as part of its value."""
        return self.flag is not None and (self.flag.multi_word or not self.flag_words[self.flag.name])
