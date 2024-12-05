from typing import Generator, List, Dict

from colorama import Fore
from .argument_parser import CliArgumentParser
from .command_argument import CommandArgument, RegionScopeArgument, BackArgument, ArgumentNames
from .input_processing import preprocess_input, FLAG, flag_arg_name
from ..domain.regional_scopes import RegionalScopes
from ..services.location import LocationService
from ..services.observation import ObservationService
from ..services.printing import PrintingService
from ..utils.logger import logger
import argparse
from prompt_toolkit.completion import Completer, Completion, WordCompleter
from prompt_toolkit.document import Document


class Command(Completer):
    def __init__(self, observation_service, location_service, printing_service):
        self.command_name = None
        self.description = None
        self.observation_service = observation_service
        self.location_service = location_service
        self.printing_service = printing_service
        self.parser = CliArgumentParser()
        self.flag_completer = None
        self.positional_completer = None
        self.arguments: List[CommandArgument] = []
        self.mandatory_params = []
        self.optional_params = []

        self.setup_arguments()

    def process_command(self, **kwargs):
        raise NotImplementedError

    def register_arguments(self):
        raise NotImplementedError

    def arg_is_multi_word(self, arg_name):
        for argument in self.arguments:
            if argument.arg_is_multi_word(arg_name):
                return True
        return False

    def handle_command(self, *args):
        processed_input = preprocess_input(' '.join(args).split())
        logger.debug(f"user input: {processed_input}")
        user_input = self.parser.parse_args(processed_input)

        kwargs: Dict[str, any] = dict()

        for argument in self.arguments:
            kwargs.update(argument.get_keywords(user_input))

        self.process_command(**kwargs)

    def find_last_flag(self, words):
        for word in reversed(words):
            if word.startswith(FLAG):
                return word
        return None

    def setup_arguments(self):
        self.register_arguments()

        for argument in self.arguments:
            self.mandatory_params.extend(argument.get_mandatory_arguments())
            self.optional_params.extend(argument.get_optional_arguments())
            argument.setup_parser(self.parser)

        self.positional_completer = WordCompleter(self.parser.positional_args, ignore_case=True)
        self.flag_completer = WordCompleter(self.parser.flag_args, ignore_case=True, match_middle=True)

    def get_completions(self, document: Document, complete_event):
        text = document.text_before_cursor
        words = text.split(" ")[1:]
        logger.debug(f"command get_completions: {words}")

        try:
            if len(words) <= len([param for param in self.mandatory_params if not param.startswith(FLAG)]):
                for completion in self.positional_completer.get_completions(document, complete_event):
                    yield Completion(completion.text, start_position=-len(document.get_word_before_cursor()))
            elif (words[-1] == "" and not words[-2].startswith(FLAG) and not self.arg_is_multi_word(self.find_last_flag(words))) or words[-1].startswith(FLAG):
                yield from self.get_flag_arg_completions(document, complete_event, words)
            else:
                yield from self.get_flag_value_completions(words, document)
        except argparse.ArgumentError as e:
            raise e.with_traceback(None)

    def get_flag_arg_completions(self, document, complete_event, words) -> Generator:
        flag_count = len([s for s in words if s.startswith(FLAG)])

        for completion in [completion for completion in self.flag_completer.get_completions(document, complete_event) if
                           completion.text not in words and (completion.text in self.mandatory_params or flag_count >= len(self.mandatory_params))]:
            if words[-1] == "":
                start_position = -len(document.get_word_before_cursor())
            else:
                text_before_cursor = document.text_before_cursor
                hyphen_index = text_before_cursor.rfind(FLAG)
                start_position = hyphen_index - len(text_before_cursor)
            yield Completion(completion.text, start_position=start_position)

    def get_flag_value_completions(self, words, document: Document) -> Generator:
        user_input = self.parser.parse_args(preprocess_input(words))

        text_before_cursor = document.text_before_cursor
        words = text_before_cursor.strip().split()
        if not words:
            return

        known_flags = set(self.parser.flag_args)

        last_flag_index = None
        for i in reversed(range(len(words))):
            if words[i] in known_flags:
                last_flag_index = i
                break

        if last_flag_index is not None and last_flag_index < len(words) - 1:
            words_after_flag = words[last_flag_index + 1:]
            start_position = -len(' '.join(words_after_flag))
        elif last_flag_index is not None:
            start_position = 0
        else:
            start_position = -len(document.get_word_before_cursor())

        for argument in self.arguments:
            if argument.supports_flag_argument_completion(words[last_flag_index]):
                yield from argument.get_flag_values(user_input, start_position)

    def print_mandatory_param(self, param_name, param_values):
        print(f"{Fore.MAGENTA}{param_name}{Fore.RESET}: {param_values}")

    def print_optional_param(self, param_name, param_values):
        print(f"{Fore.CYAN}{param_name}{Fore.RESET}: {param_values}")

    def print_description(self):
        print(f"{self.command_example()}")
        print()
        print(self.description)
        print()

    def command_example(self):
        command_name = f"{Fore.RED}{self.command_name}{Fore.RESET}"
        mandatory_params = f"{Fore.MAGENTA}<{', '.join(self.mandatory_params)}>{Fore.RESET}" if len(self.mandatory_params) else ""
        optional_params = f"{Fore.CYAN}[{', '.join(self.optional_params)}]{Fore.RESET}" if len(self.optional_params) > 0 else ""

        return f"{command_name:18} {mandatory_params} {optional_params}"


class ObservationCommand(Command):
    pass

    scope_arg = str(ArgumentNames.SCOPE.value)
    region_arg = str(ArgumentNames.REGION.value)
    back_arg = str(ArgumentNames.BACK.value)

    def process_command(self, **kwargs):
        logger.debug(f"process_command - kwargs: {kwargs}")

        region = kwargs[self.region_arg]
        scope = kwargs[self.scope_arg]
        days_back = kwargs[self.back_arg]

        self.handle_observations(region, scope, days_back)

    def register_arguments(self):
        self.arguments = [RegionScopeArgument(self.location_service),
                          BackArgument()]

    def handle_observations(self, region, scope, back):
        raise NotImplementedError


class RecentCommand(ObservationCommand):
    def __init__(self, observation_service: ObservationService, location_service: LocationService, printing_service: PrintingService):
        super().__init__(observation_service, location_service, printing_service)

        self.command_name = "recent"
        self.description = "Retrieve recent observations for the specified region"

    def handle_observations(self, region, scope, back):
        if scope == RegionalScopes.NEARBY.value:
            observations = self.observation_service.get_nearby_recent_observations(back)
        else:
            observations = self.observation_service.get_recent_observations(self.location_service.get_region_ids_by_scope(region, scope))

        self.printing_service.print_recent(observations)


class NotableCommand(ObservationCommand):
    def __init__(self, observation_service: ObservationService, location_service: LocationService, printing_service: PrintingService):
        super().__init__(observation_service, location_service, printing_service)

        self.command_name = "notable"
        self.description = "Retrieve notable observations for the specified region"

    def handle_observations(self, region, scope: str, back):
        if scope == RegionalScopes.NEARBY.value:
            observations = self.observation_service.get_nearby_notable_observations(back)
        else:
            observations = self.observation_service.get_notable_observations(self.location_service.get_region_ids_by_scope(region, scope))

        self.printing_service.print_notable(observations)
