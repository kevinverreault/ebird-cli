import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

import pytest
from fakes import FakeEbirdClient, ScriptedAsk
from prompt_toolkit.completion import CompleteEvent
from prompt_toolkit.document import Document
from rich.console import Console

from ebird_cli import download_lists as download_lists_module
from ebird_cli import settings as settings_module
from ebird_cli.cli.autocomplete import ContextSensitiveCompleter
from ebird_cli.cli.command import NotableCommand, RecentCommand, SettingsCommand
from ebird_cli.domain.region import Region
from ebird_cli.services import cache as cache_module
from ebird_cli.services.cache import CacheService
from ebird_cli.services.location_catalogue import LocationCatalogue
from ebird_cli.services.observation_query import ObservationQuery
from ebird_cli.services.printing import PrintingService
from ebird_cli.services.taxonomy import TaxonomyService
from ebird_cli.settings import SettingsFile, reconfigure
from ebird_cli.utils import logger as logger_module

FIXTURES = Path(__file__).parent / "fixtures"
REGION = "CA-QC-MR"
LAT = "46.35"
LONG = "-72.55"

ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*m")
ANSI_COLORS = {"31": "red", "32": "green", "37": "white"}


def copy_fixture_cache(cache_dir: Path):
    """Copy the fixture cache into cache_dir as if just written, so no cached file has expired."""
    shutil.copytree(FIXTURES / "cache", cache_dir, dirs_exist_ok=True, copy_function=shutil.copy)


@pytest.fixture(autouse=True)
def offline_and_isolated(monkeypatch):
    """Fail loudly if a test would reach the real eBird API or website or the real user cache, log or config
    directory, and unset the settings' environment variables of the shell running the tests."""

    def forbidden(*_args, **_kwargs):
        raise AssertionError(
            "tests must inject a fake eBird client, a fake HTTP session and temporary cache, log and config directories"
        )

    monkeypatch.setattr(cache_module, "user_cache_dir", forbidden)
    monkeypatch.setattr(cache_module, "EbirdClient", forbidden)
    monkeypatch.setattr(logger_module, "user_log_dir", forbidden)
    monkeypatch.setattr(settings_module, "user_config_dir", forbidden)
    for setting in settings_module.SETTINGS:
        monkeypatch.delenv(setting.env_variable, raising=False)
    monkeypatch.setattr(download_lists_module, "Session", forbidden)


def strip_ansi(text: str) -> str:
    return ANSI_ESCAPE.sub("", text)


def table_rows(output: str) -> list[list[str]]:
    """Body rows of the printed observation table, as lists of cell texts."""
    return [
        [cell.strip() for cell in line.strip().strip("│").split("│")]
        for line in strip_ansi(output).splitlines()
        if line.startswith("│")
    ]


def table_header(output: str) -> list[str]:
    header = next(line for line in strip_ansi(output).splitlines() if line.startswith("┃"))
    return [cell.strip() for cell in header.strip().strip("┃").split("┃")]


def highlight_of(name: str, output: str) -> str:
    """Colour the observation table printed a species name in."""
    match = re.search(r"\x1b\[(\d+)m" + re.escape(name), output)
    assert match, f"{name} was not printed with a colour"
    return ANSI_COLORS[match.group(1)]


@dataclass
class Cli:
    client: FakeEbirdClient
    commands: dict
    completer: ContextSensitiveCompleter
    location_catalogue: LocationCatalogue
    taxonomy_service: TaxonomyService
    settings_file: SettingsFile
    ask: ScriptedAsk

    def run(self, line: str):
        command_name, *command_args = line.split()
        self.commands[command_name].handle_command(*command_args)

    def completions(self, text: str) -> list[str]:
        document = Document(text, len(text))
        return [completion.text for completion in self.completer.get_completions(document, CompleteEvent())]


@pytest.fixture
def make_cli(tmp_path):
    """Wire real services and commands the way main does, over fixture caches and a fake eBird client."""

    def make(client=None, aggregations=None, year_list=None, life_list=None, lat=LAT, long=LONG, ask=None) -> Cli:
        client = client or FakeEbirdClient()
        ask = ask or ScriptedAsk()
        settings_file = SettingsFile(tmp_path / "config" / "settings.json")
        cache_dir = tmp_path / "cache"
        copy_fixture_cache(cache_dir)

        cache_service = CacheService("api-key", "fr", Region(REGION), api_client=client, cache_dir=str(cache_dir))
        console = Console(force_terminal=True, color_system="standard", width=200, legacy_windows=False)
        printing_service = PrintingService(life_list, year_list, console=console)
        location_catalogue = LocationCatalogue.load(Region(REGION), client, str(cache_dir), aggregations)
        observation_query = ObservationQuery(client, location_catalogue, lat, long)
        taxonomy_service = TaxonomyService(cache_service.taxonomy_cache)

        commands = {
            command.command_name: command
            for command in [
                RecentCommand(observation_query, location_catalogue, printing_service, taxonomy_service),
                NotableCommand(observation_query, location_catalogue, printing_service),
                SettingsCommand(lambda: reconfigure(settings_file, ask, os.environ)),
            ]
        }
        completer = ContextSensitiveCompleter(commands.values())
        return Cli(client, commands, completer, location_catalogue, taxonomy_service, settings_file, ask)

    return make


@pytest.fixture
def cli(make_cli) -> Cli:
    return make_cli()
