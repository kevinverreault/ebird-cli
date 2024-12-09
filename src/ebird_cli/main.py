import argparse
import os
import re

from .services.cache import CacheService
from .services.location import LocationService
from .services.printing import PrintingService
from .services.observation import ObservationService
from .domain.region import Region
from .cli.command import RecentCommand, NotableCommand
from .cli.autocomplete import ContextSensitiveCompleter
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from colorama import Fore

api_key_env_variable = "EBIRDAPIKEY"
locale_env_variable = "EBIRDLOCALE"
default_region_env_variable = "EBIRDDEFAULTREGION"
year_list_env_variable = "EBIRDYEARLIST"
life_list_env_variable = "EBIRDLIFELIST"
lat_env_variable = "EBIRDLAT"
long_env_variable = "EBIRDLONG"

region_regex = "([A-Z]{2}-){2}[A-Z]{2}"


def regex_type(pattern: str | re.Pattern):
    def closure_check_regex(arg_value):
        if not re.match(pattern, arg_value):
            raise argparse.ArgumentTypeError("invalid value")
        return arg_value

    return closure_check_regex


def print_menu(commands):
    examples = []

    for key, value in commands.items():
        examples.append(value.command_example())
    formatted_examples = '\n    '.join(f"{item}" for item in examples)
    menu = f"""
    {Fore.GREEN}eBird CLI{Fore.RESET}
    
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


def setup_parser(parser: argparse.ArgumentParser):
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
        help="eBird subnational level 2 region code",
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

    cache_service = CacheService(api_key, locale, Region(region))
    observation_service = ObservationService(api_key, locale, lat, long)
    printing_service = PrintingService(life_list, year_list)
    location_service = LocationService(cache_service.location_cache)

    commands = {command.command_name: command for command in
                [cls(observation_service, location_service, printing_service) for cls in [RecentCommand, NotableCommand]]}

    style = Style.from_dict({
        'prompt': 'ansigreen bold',
        '': 'ansiwhite',
        'completion-menu.completion': 'bg:#008888 #ffffff',
        'completion-menu.completion.current': 'bg:#00aaaa #000000',
    })

    print_menu(commands)
    session = PromptSession(completer=ContextSensitiveCompleter(commands.values()), key_bindings=setup_key_bindings())

    while True:
        try:
            print("")
            user_input = session.prompt(f"⋙  ", style=style)
            if user_input.lower() == "exit" or user_input.lower() == "e":
                print("Exiting eBird CLI.")
                break

            if user_input == "":
                print_menu(commands)
                continue

            args = user_input.split()
            if not args:
                continue

            command_name, *command_args = args
            user_request = commands.get(command_name)

            if user_request:
                user_request.handle_command(*command_args)
            else:
                print("Unknown command.")
        except KeyboardInterrupt:
            continue
        except EOFError:
            break
        except argparse.ArgumentError as e:
            print(f"Invalid argument: {e.message}")
        except Exception as e:
            print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
