from collections.abc import Callable
from dataclasses import dataclass

from colorama import Fore
from prompt_toolkit.completion import Completion
from prompt_toolkit.document import Document

from ..domain.match import contains
from ..domain.regional_scopes import RegionalScopes
from ..services.location_catalogue import LocationCatalogue
from ..services.observation_query import ObservationKind, ObservationQuery
from ..services.printing import PrintingService
from ..services.taxonomy import TaxonomyService
from ..utils.logger import logger
from .grammar import Arguments, Flag, Grammar, Positional

SCOPE = Positional("scope", choices=[scope.value for scope in RegionalScopes])
BACK = Flag("back", default="7", choices=range(1, 31))


def region_flag(location_catalogue: LocationCatalogue) -> Flag:
    return Flag(
        "region",
        multi_word=True,
        suggestions=lambda typed, arguments: location_catalogue.names(RegionalScopes(arguments["scope"]), typed),
        hidden_when=lambda arguments: arguments.get("scope") == RegionalScopes.NEARBY,
    )


def species_flag(taxonomy_service: TaxonomyService) -> Flag:
    return Flag(
        "species",
        multi_word=True,
        suggestions=lambda typed, _arguments: taxonomy_service.search_by_common_name(typed) if typed else [],
    )


class Command:
    def __init__(self, command_name: str, description: str, grammar: Grammar):
        self.command_name = command_name
        self.description = description
        self.grammar = grammar

    def run(self, arguments: Arguments):
        raise NotImplementedError

    def handle_command(self, *args):
        logger.debug(f"user input: {args}")
        self.run(self.grammar.parse(list(args)))

    def get_completions(self, document: Document, _complete_event):
        _command_name, _, text = document.text_before_cursor.partition(" ")
        logger.debug(f"command get_completions: {text}")
        yield from self.grammar.complete(text)

    def command_example(self):
        command_name = f"{Fore.RED}{self.command_name}{Fore.RESET}"
        mandatory = [positional.name for positional in self.grammar.positionals]
        optional = [flag.token for flag in self.grammar.flags]
        mandatory_params = f"{Fore.MAGENTA}<{', '.join(mandatory)}>{Fore.RESET}" if mandatory else ""
        optional_params = f"{Fore.CYAN}[{', '.join(optional)}]{Fore.RESET}" if optional else ""

        return f"{command_name:18} {mandatory_params} {optional_params}"


@dataclass
class ObservationCommandArgs:
    region: str | None
    scope: RegionalScopes
    back: str
    species: str | None = None


class ObservationCommand(Command):
    kind: ObservationKind

    def __init__(
        self,
        command_name: str,
        description: str,
        grammar: Grammar,
        observation_query: ObservationQuery,
        printing_service: PrintingService,
    ):
        super().__init__(command_name, description, grammar)
        self.observation_query = observation_query
        self.printing_service = printing_service

    def run(self, arguments: Arguments):
        logger.debug(f"run - arguments: {arguments}")
        args = ObservationCommandArgs(
            region=arguments["region"],
            scope=RegionalScopes(arguments["scope"]),
            back=arguments["back"],
            species=arguments.get("species"),
        )
        self.handle_observation(args)

    def handle_observation(self, args: ObservationCommandArgs):
        self.print_observations(args)

    def print_observations(self, args: ObservationCommandArgs, species_code: str | None = None):
        observations = self.observation_query.observations(
            self.kind, args.scope, args.region, species_code=species_code, back=args.back
        )
        self.printing_service.print_observations(observations)


class RecentCommand(ObservationCommand):
    kind = ObservationKind.RECENT

    def __init__(
        self,
        observation_query: ObservationQuery,
        location_catalogue: LocationCatalogue,
        printing_service: PrintingService,
        taxonomy_service: TaxonomyService,
    ):
        super().__init__(
            "recent",
            "Retrieve recent observations for the specified region",
            Grammar([SCOPE], [region_flag(location_catalogue), species_flag(taxonomy_service), BACK]),
            observation_query,
            printing_service,
        )
        self.taxonomy_service = taxonomy_service

    def handle_observation(self, args: ObservationCommandArgs):
        species_code = None
        if args.species:
            species_codes = self.taxonomy_service.get_species_code(args.species)
            if not species_codes:
                return
            species_code = species_codes[0]
        self.print_observations(args, species_code)


class NotableCommand(ObservationCommand):
    kind = ObservationKind.NOTABLE

    def __init__(
        self,
        observation_query: ObservationQuery,
        location_catalogue: LocationCatalogue,
        printing_service: PrintingService,
    ):
        super().__init__(
            "notable",
            "Retrieve notable observations for the specified region",
            Grammar([SCOPE], [region_flag(location_catalogue), BACK]),
            observation_query,
            printing_service,
        )


class FindCommand(Command):
    """Find text in the Last result, without contacting eBird."""

    def __init__(self, printing_service: PrintingService):
        super().__init__("find", "Find text in the observations of the last recent or notable command", Grammar([], []))
        self.printing_service = printing_service

    def handle_command(self, *args):
        logger.debug(f"user input: {args}")
        self.printing_service.print_matches(" ".join(args))

    def command_example(self):
        command_name = f"{Fore.RED}{self.command_name}{Fore.RESET}"
        return f"{command_name:18} {Fore.CYAN}[text]{Fore.RESET} (Ctrl+F)"

    def get_completions(self, document: Document, _complete_event):
        """The species, then the location names of the Last result containing what was typed after find."""
        _command_name, _, typed = document.text_before_cursor.partition(" ")
        typed = typed.lstrip()
        logger.debug(f"find get_completions: {typed}")
        observations = self.printing_service.last_result or []
        names = dict.fromkeys([obs.name for obs in observations] + [obs.location for obs in observations])
        for name in names:
            if contains(name, " ".join(typed.split())):
                yield Completion(name, start_position=-len(typed))


class SettingsCommand(Command):
    """Reconfigure the saved settings without leaving the prompt; this session keeps the settings it started with."""

    def __init__(self, reconfigure: Callable[[], bool]):
        super().__init__("settings", "Change the saved settings for the next launch", Grammar([], []))
        self.reconfigure = reconfigure

    def run(self, _arguments: Arguments):
        if self.reconfigure():
            print("Changes apply on the next launch.")
