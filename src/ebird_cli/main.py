import argparse
import os
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
from .settings import Settings, SettingsError, add_arguments, resolve
from .utils.logger import configure_logging


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
    add_arguments(parser)


def read_settings(parser: argparse.ArgumentParser, args: argparse.Namespace, saved) -> Settings:
    """The settings of this launch, exiting with a usage error when they cannot start it."""
    try:
        return resolve(args, os.environ, saved)
    except SettingsError as e:
        parser.error(e.message)


def main():
    configure_logging()

    parser = argparse.ArgumentParser(description="eBird CLI")
    setup_parser(parser)

    settings = read_settings(parser, parser.parse_args(), None)

    api_key = settings.api_key
    region = settings.region
    locale = settings.locale
    lat = settings.lat
    long = settings.long

    life_list = settings.life_list
    year_list = settings.year_list
    aggregations = settings.aggregations

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

    print_menu(commands, settings)
    session = PromptSession(completer=ContextSensitiveCompleter(commands.values()), key_bindings=setup_key_bindings())

    while True:
        try:
            print("")
            user_input = session.prompt("⋙  ", style=style)
            if not handle_input(user_input, commands, settings):
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
