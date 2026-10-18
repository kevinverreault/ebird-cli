import argparse
import os
import re
import ssl
import urllib.request
from importlib.metadata import version

import certifi
from appdirs import user_cache_dir
from colorama import Fore
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.styles import Style

from .cli.autocomplete import ContextSensitiveCompleter
from .cli.command import NotableCommand, RecentCommand
from .cli.grammar import CommandLineError
from .domain.region import Region
from .services.cache import CacheService
from .services.ebird_client import EbirdClient
from .services.location_catalogue import LocationCatalogue
from .services.observation_query import ObservationQuery
from .services.printing import PrintingService
from .services.taxonomy import TaxonomyService

api_key_env_variable = "EBIRDAPIKEY"
locale_env_variable = "EBIRDLOCALE"
default_region_env_variable = "EBIRDDEFAULTREGION"
year_list_env_variable = "EBIRDYEARLIST"
life_list_env_variable = "EBIRDLIFELIST"
lat_env_variable = "EBIRDLAT"
long_env_variable = "EBIRDLONG"
aggregations_env_variable = "EBIRDAGGREGATIONS"

region_regex = "([A-Z]{2}-){2}[A-Z]{2}"


def regex_type(pattern: str | re.Pattern):
    def closure_check_regex(arg_value):
        if not re.match(pattern, arg_value):
            raise argparse.ArgumentTypeError("invalid value")
        return arg_value

    return closure_check_regex


def print_menu(commands, args=None):
    examples = []

    for value in commands.values():
        examples.append(value.command_example())
    formatted_examples = "\n    ".join(f"{item}" for item in examples)

    args_section = ""
    if args is not None:
        arg_lines = [
            f"{Fore.BLUE}region{Fore.RESET}: {args.region}",
            f"{Fore.BLUE}locale{Fore.RESET}: {args.locale}",
        ]
        args_section = "\n    Arguments:\n    \n    " + "\n    ".join(arg_lines) + "\n    "

    menu = f"""
    {Fore.GREEN}eBird CLI{Fore.RESET}
    {args_section}
    Available commands:

    {formatted_examples}
    """

    print(menu)


def setup_key_bindings():
    bindings = KeyBindings()

    @bindings.add(Keys.Tab)
    def handle_tab(event):
        buffer = event.app.current_buffer
        if buffer.complete_state:
            buffer.complete_next()
        else:
            buffer.start_completion(select_first=True)

    return bindings


def use_certifi_ca_bundle():
    # ebird-api calls urllib's urlopen, which on Windows only trusts roots already in the Windows store.
    # Windows downloads roots on demand, so eBird's root may be missing; use certifi's bundle like requests does.
    context = ssl.create_default_context(cafile=certifi.where())
    urllib.request.install_opener(urllib.request.build_opener(urllib.request.HTTPSHandler(context=context)))


def setup_parser(parser: argparse.ArgumentParser):
    parser.add_argument("--version", action="version", version=f"ebird-cli {version('ebird-cli')}")

    parser.add_argument(
        "--api-key",
        default=os.getenv(api_key_env_variable),
        required=os.getenv(api_key_env_variable) is None,
        help=f"eBird API key (mandatory if {api_key_env_variable} env variable is not set)",
    )

    parser.add_argument(
        "--region",
        default=os.getenv(default_region_env_variable),
        required=os.getenv(default_region_env_variable) is None,
        help=(
            "eBird subnational level 2 region code is mandatory if "
            f"{default_region_env_variable} env variable is not set"
        ),
        type=regex_type(region_regex),
    )

    parser.add_argument(
        "--locale",
        type=str,
        default=os.getenv(locale_env_variable) if os.getenv(locale_env_variable) is not None else "fr",
        help="Locale",
    )

    parser.add_argument(
        "--lat",
        type=str,
        default=os.getenv(lat_env_variable),
        help="Latitude",
    )

    parser.add_argument(
        "--long",
        type=str,
        default=os.getenv(long_env_variable),
        help="Longitude",
    )

    parser.add_argument(
        "--year-list",
        type=str,
        default=os.getenv(year_list_env_variable),
        help="List of observations for the current year",
    )

    parser.add_argument(
        "--life-list",
        type=str,
        default=os.getenv(life_list_env_variable),
        help="List of lifetime observations",
    )

    parser.add_argument(
        "--aggregations",
        type=str,
        default=os.getenv(aggregations_env_variable),
        help=f"Path to aggregations JSON file (custom hotspot groups). From {aggregations_env_variable} env var",
    )


def main():
    parser = argparse.ArgumentParser(description="eBird CLI")
    setup_parser(parser)

    args = parser.parse_args()

    api_key = args.api_key
    region = args.region
    locale = args.locale
    lat = args.lat
    long = args.long

    life_list = args.life_list or None
    year_list = args.year_list or None
    aggregations = args.aggregations or None

    use_certifi_ca_bundle()

    client = EbirdClient(api_key, locale)
    cache_dir = user_cache_dir("ebird_cli")

    cache_service = CacheService(api_key, locale, Region(region), api_client=client, cache_dir=cache_dir)
    printing_service = PrintingService(life_list, year_list)
    location_catalogue = LocationCatalogue.load(Region(region), client, cache_dir, aggregations)
    observation_query = ObservationQuery(client, location_catalogue, lat, long)
    taxonomy_service = TaxonomyService(cache_service.taxonomy_cache)

    commands = {
        command.command_name: command
        for command in [
            RecentCommand(observation_query, location_catalogue, printing_service, taxonomy_service),
            NotableCommand(observation_query, location_catalogue, printing_service),
        ]
    }

    style = Style.from_dict(
        {
            "prompt": "ansigreen bold",
            "": "ansiwhite",
            "completion-menu.completion": "bg:#008888 #ffffff",
            "completion-menu.completion.current": "bg:#00aaaa #000000",
        }
    )

    print_menu(commands, args)
    session = PromptSession(completer=ContextSensitiveCompleter(commands.values()), key_bindings=setup_key_bindings())

    while True:
        try:
            print("")
            user_input = session.prompt("⋙  ", style=style)
            if not handle_input(user_input, commands, args):
                break
        except KeyboardInterrupt:
            continue
        except EOFError:
            break


def handle_input(user_input: str, commands, program_args) -> bool:
    """Run one line typed at the prompt. Returns whether the session should continue."""
    try:
        if user_input.lower() == "exit" or user_input.lower() == "e":
            print("Exiting eBird CLI.")
            return False

        if user_input == "":
            print_menu(commands, program_args)
            return True

        words = user_input.split()
        if not words:
            return True

        command_name, *command_args = words
        user_request = commands.get(command_name)

        if user_request:
            user_request.handle_command(*command_args)
        else:
            print("Unknown command.")
    except CommandLineError as e:
        print(f"Invalid argument: {e.message}")
    except Exception as e:
        print(f"An error occurred: {e}")

    return True


if __name__ == "__main__":
    main()
