import re
import shutil
from dataclasses import dataclass
from pathlib import Path

import pytest
from fakes import FakeEbirdClient
from prompt_toolkit.completion import CompleteEvent
from prompt_toolkit.document import Document
from rich.console import Console

from ebird_cli.cli.autocomplete import ContextSensitiveCompleter
from ebird_cli.cli.command import NotableCommand, RecentCommand
from ebird_cli.domain.region import Region
from ebird_cli.services import cache as cache_module
from ebird_cli.services import observation as observation_module
from ebird_cli.services.cache import CacheService
from ebird_cli.services.location import LocationService
from ebird_cli.services.observation import ObservationService
from ebird_cli.services.printing import PrintingService
from ebird_cli.services.taxonomy import TaxonomyService

FIXTURES = Path(__file__).parent / "fixtures"
REGION = "CA-QC-MR"
LAT = "46.35"
LONG = "-72.55"

ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*m")
ANSI_COLORS = {"31": "red", "32": "green", "37": "white"}


@pytest.fixture(autouse=True)
def offline_and_isolated(monkeypatch):
    """Fail loudly if a test would reach the real eBird API or the real user cache directory."""

    def forbidden(*_args, **_kwargs):
        raise AssertionError("tests must inject a fake eBird client and a temporary cache directory")

    monkeypatch.setattr(cache_module, "user_cache_dir", forbidden)
    monkeypatch.setattr(cache_module, "EbirdClient", forbidden)
    monkeypatch.setattr(observation_module, "EbirdClient", forbidden)


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
    location_service: LocationService
    taxonomy_service: TaxonomyService

    def run(self, line: str):
        command_name, *command_args = line.split()
        self.commands[command_name].handle_command(*command_args)

    def completions(self, text: str) -> list[str]:
        document = Document(text, len(text))
        return [completion.text for completion in self.completer.get_completions(document, CompleteEvent())]


@pytest.fixture
def make_cli(tmp_path):
    """Wire real services and commands the way main does, over fixture caches and a fake eBird client."""

    def make(client=None, aggregations=None, year_list=None, life_list=None, lat=LAT, long=LONG) -> Cli:
        client = client or FakeEbirdClient()
        cache_dir = tmp_path / "cache"
        shutil.copytree(FIXTURES / "cache", cache_dir, dirs_exist_ok=True)

        cache_service = CacheService("api-key", "fr", Region(REGION), api_client=client, cache_dir=str(cache_dir))
        observation_service = ObservationService("api-key", "fr", lat, long, api_client=client)
        console = Console(force_terminal=True, color_system="standard", width=200, legacy_windows=False)
        printing_service = PrintingService(life_list, year_list, console=console)
        location_service = LocationService(cache_service.location_cache, aggregations)
        taxonomy_service = TaxonomyService(cache_service.taxonomy_cache)

        commands = {command.command_name: command for command in [
            RecentCommand(observation_service, location_service, printing_service, taxonomy_service),
            NotableCommand(observation_service, location_service, printing_service),
        ]}
        return Cli(client, commands, ContextSensitiveCompleter(commands.values()), location_service, taxonomy_service)

    return make


@pytest.fixture
def cli(make_cli) -> Cli:
    return make_cli()
