"""The program settings: one definition per setting, and their resolution from flags and saved values."""

import argparse
import json
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path

from appdirs import user_config_dir
from prompt_toolkit import prompt

REGION_PATTERN = "[A-Z]{2}-[A-Z0-9]{1,3}-[A-Z0-9]{1,3}"


class SettingsError(Exception):
    """Settings that cannot start a launch: a required one is missing, or one has an invalid value."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


@dataclass(frozen=True)
class Setting:
    """A setting, read from its flag, then saved settings, then its default.

    A value given must match pattern, when the setting has one; example shows a value that does. label names the
    setting when setup asks for it.
    """

    name: str
    label: str
    description: str
    default: str | None = None
    required: bool = False
    pattern: str | None = None
    example: str | None = None

    @property
    def flag(self) -> str:
        return "--" + self.name.replace("_", "-")

    def accepts(self, value: str) -> bool:
        return self.pattern is None or re.fullmatch(self.pattern, value) is not None

    @property
    def question(self) -> str:
        if self.required:
            hint = f" (required, like {self.example})" if self.example else " (required)"
        else:
            hint = f" (default {self.default})" if self.default else " (optional)"
        return f"{self.label}{hint}: "


SETTINGS = (
    Setting("api_key", "eBird API key", "eBird API key", required=True),
    Setting(
        "region",
        "Home Region",
        "Home Region, an eBird subnational level 2 region code",
        required=True,
        pattern=REGION_PATTERN,
        example="CA-QC-MR",
    ),
    Setting("locale", "Locale", "Locale", default="fr"),
    Setting("lat", "Latitude", "Latitude"),
    Setting("long", "Longitude", "Longitude"),
    Setting("year_list", "Year list path", "List of observations for the current year"),
    Setting("life_list", "Life list path", "List of lifetime observations"),
    Setting(
        "aggregations",
        "Aggregations path",
        "Path to aggregations JSON file (named groups of Hotspots)",
    ),
)

Ask = Callable[[str, str], str]
"""Asks the user a question with an editable pre-filled answer, and returns what they enter."""


def ask_in_terminal(question: str, default: str) -> str:
    return prompt(question, default=default)


@dataclass(frozen=True)
class Settings:
    api_key: str
    region: str
    locale: str
    lat: str | None
    long: str | None
    year_list: str | None
    life_list: str | None
    aggregations: str | None


class SettingsFile:
    """The saved settings, a JSON object in the user config directory by default.

    That directory is apart from the user cache directory, so deleting the cache keeps the settings.
    """

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path is not None else Path(user_config_dir("ebird_cli")) / "settings.json"

    def load(self) -> dict[str, str] | None:
        """The saved settings, or None when none were ever saved."""
        if not self.path.exists():
            return None
        try:
            saved = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise SettingsError(f"saved settings in {self.path} are not valid JSON: {e}") from e
        if not isinstance(saved, dict) or not all(isinstance(value, str) for value in saved.values()):
            raise SettingsError(f"saved settings in {self.path} must be a JSON object of text values")
        return saved

    def save(self, values: Mapping[str, str]):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(dict(values), indent=2) + "\n", encoding="utf-8")


def add_arguments(parser: argparse.ArgumentParser):
    """Add a flag per setting. None of them is required: a missing value may come from another source."""
    for setting in SETTINGS:
        parser.add_argument(
            setting.flag,
            dest=setting.name,
            type=argument_type(setting),
            help=f"{setting.description} (or saved settings" + (f", or {setting.default})" if setting.default else ")"),
        )


def argument_type(setting: Setting):
    def check(value: str) -> str:
        if not setting.accepts(value):
            raise argparse.ArgumentTypeError("invalid value")
        return value

    return check


def supplied(args: argparse.Namespace) -> dict[str, str]:
    """The value each setting gets from its flag."""
    values = {}
    for setting in SETTINGS:
        value = getattr(args, setting.name, None)
        if value:
            values[setting.name] = value
    return values


def resolve(args: argparse.Namespace, saved: Mapping[str, str] | None) -> Settings:
    """Each setting from its flag, else saved settings, else its default."""
    values = {**(saved or {}), **supplied(args)}
    resolved = {}
    for setting in SETTINGS:
        value = values.get(setting.name) or setting.default
        if value is None and setting.required:
            raise SettingsError(f"{setting.flag} is required: set it or run ebird-cli settings")
        if value is not None and not setting.accepts(value):
            raise SettingsError(f"{setting.flag}: invalid value {value!r}")
        resolved[setting.name] = value
    return Settings(**resolved)


def run_setup(prefill: Mapping[str, str], ask: Ask) -> dict[str, str]:
    """Ask for each setting, pre-filled from prefill, and return the non-empty answers.

    Re-asks while a required setting is empty or an answer is invalid. Ctrl+C and Ctrl+D raise to the caller.
    """
    answers = {}
    for setting in SETTINGS:
        while True:
            answer = ask(setting.question, prefill.get(setting.name, "")).strip()
            if not answer and setting.required:
                print(f"{setting.label} is required.")
            elif answer and not setting.accepts(answer):
                print(f"{setting.label} must look like {setting.example}.")
            else:
                break
        if answer:
            answers[setting.name] = answer
    return answers


def first_launch_setup(settings_file: SettingsFile, prefill: Mapping[str, str], ask: Ask) -> dict[str, str] | None:
    """Run setup and save the answers, or save nothing and return None when the user interrupts it."""
    print(f"Welcome to eBird CLI. Answer a few questions to set it up; they are saved to {settings_file.path}.")
    try:
        answers = run_setup(prefill, ask)
    except (KeyboardInterrupt, EOFError):
        print("Setup interrupted: nothing was saved.")
        return None
    settings_file.save(answers)
    return answers


def reconfigure(settings_file: SettingsFile, ask: Ask) -> bool:
    """Rerun setup pre-filled with the saved settings and overwrite them; returns whether they were saved.

    Unreadable saved settings pre-fill nothing. Interrupting leaves them untouched.
    """
    try:
        saved = settings_file.load() or {}
    except SettingsError:
        saved = {}
    try:
        answers = run_setup(saved, ask)
    except (KeyboardInterrupt, EOFError):
        print("Settings unchanged.")
        return False
    settings_file.save(answers)
    print(f"Settings saved to {settings_file.path}.")
    return True
