"""The program settings: one definition per setting, and their resolution from flags, environment and saved values."""

import argparse
import re
from collections.abc import Mapping
from dataclasses import dataclass

REGION_PATTERN = "([A-Z]{2}-){2}[A-Z]{2}"


class SettingsError(Exception):
    """Settings that cannot start a launch: a required one is missing, or one has an invalid value."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


@dataclass(frozen=True)
class Setting:
    """A setting, read from its flag, then its environment variable, then saved settings, then its default.

    A value given must match pattern, when the setting has one.
    """

    name: str
    env_variable: str
    description: str
    default: str | None = None
    required: bool = False
    pattern: str | None = None

    @property
    def flag(self) -> str:
        return "--" + self.name.replace("_", "-")

    def accepts(self, value: str) -> bool:
        return self.pattern is None or re.match(self.pattern, value) is not None


SETTINGS = (
    Setting("api_key", "EBIRDAPIKEY", "eBird API key", required=True),
    Setting(
        "region",
        "EBIRDDEFAULTREGION",
        "Home Region, an eBird subnational level 2 region code (CA-QC-MR)",
        required=True,
        pattern=REGION_PATTERN,
    ),
    Setting("locale", "EBIRDLOCALE", "Locale", default="fr"),
    Setting("lat", "EBIRDLAT", "Latitude"),
    Setting("long", "EBIRDLONG", "Longitude"),
    Setting("year_list", "EBIRDYEARLIST", "List of observations for the current year"),
    Setting("life_list", "EBIRDLIFELIST", "List of lifetime observations"),
    Setting("aggregations", "EBIRDAGGREGATIONS", "Path to aggregations JSON file (custom hotspot groups)"),
)


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


def add_arguments(parser: argparse.ArgumentParser):
    """Add a flag per setting. None of them is required: a missing value may come from another source."""
    for setting in SETTINGS:
        parser.add_argument(
            setting.flag,
            dest=setting.name,
            type=argument_type(setting),
            help=f"{setting.description} (or {setting.env_variable}, or saved settings)",
        )


def argument_type(setting: Setting):
    def check(value: str) -> str:
        if not setting.accepts(value):
            raise argparse.ArgumentTypeError("invalid value")
        return value

    return check


def supplied(args: argparse.Namespace, environ: Mapping[str, str]) -> dict[str, str]:
    """The value each setting gets from its flag or, without one, its environment variable."""
    values = {}
    for setting in SETTINGS:
        value = getattr(args, setting.name, None) or environ.get(setting.env_variable)
        if value:
            values[setting.name] = value
    return values


def resolve(args: argparse.Namespace, environ: Mapping[str, str], saved: Mapping[str, str] | None) -> Settings:
    """Each setting from its flag, else its environment variable, else saved settings, else its default."""
    values = {**(saved or {}), **supplied(args, environ)}
    resolved = {}
    for setting in SETTINGS:
        value = values.get(setting.name) or setting.default
        if value is None and setting.required:
            raise SettingsError(f"{setting.flag} is required: set it, {setting.env_variable} or saved settings")
        if value is not None and not setting.accepts(value):
            raise SettingsError(f"{setting.flag}: invalid value {value!r}")
        resolved[setting.name] = value
    return Settings(**resolved)
