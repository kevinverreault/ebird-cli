import datetime
import os
from prompt_toolkit.shortcuts import input_dialog
from .services.location import LocationService
from .services.printing import PrintingService
from .services.observation import ObservationService
from .cli.command import Command
from .cli.autocomplete import ContextSensitiveCompleter
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from colorama import Fore

api_key_env_variable = "EBIRDAPIKEY"
locale_env_variable = "EBIRDLOCALE"
year_list_env_variable = "EBIRDYEARLIST"
life_list_env_variable = "EBIRDLIFELIST"


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


def main():
    key_input = ""
    if os.getenv(api_key_env_variable) is None:
        print(f"{api_key_env_variable} not set.")
        key_input = input_dialog(
            title='eBird API key',
            text='Please type your eBird API key:').run()

    api_key = os.getenv(api_key_env_variable) or key_input
    locale = os.getenv(locale_env_variable) or "en"
    observation_service = ObservationService(api_key, locale)

    life_list = os.getenv(life_list_env_variable) or '~/ebird_data/life_list.csv'  # None
    year_list = os.getenv(year_list_env_variable) or f"~/ebird_data/ebird_CA-QC_year_{datetime.datetime.now().year}_list.csv"  # None
    printing_service = PrintingService(life_list, year_list)

    location_service = LocationService("CA-QC-MR")

    commands = {cls.command_name: cls(observation_service, printing_service, location_service) for cls in Command.__subclasses__()}

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
            if user_input.lower() == "exit":
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
        except Exception as e:
            print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
