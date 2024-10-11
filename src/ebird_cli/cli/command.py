from abc import ABC
from colorama import Fore
from .argument_parser import CliArgumentParser
from ..domain.regional_scopes import RegionalScopes
from ..services.location import LocationService
from ..services.observation import ObservationService
from ..services.printing import PrintingService
from ..utils.logger import logger
import argparse
from prompt_toolkit.completion import Completer, Completion, WordCompleter
from prompt_toolkit.document import Document

FLAG: str = "-"


class Command(Completer):
    command_name = None
    mandatory_params = []
    optional_params = []
    description = None
    positional_completer: WordCompleter = None
    flagged_completer: WordCompleter = None

    def __init__(self, observation_service: ObservationService, printing_service: PrintingService, location_service: LocationService):
        self.setup_params()
        self.observation_service = observation_service
        self.printing_service = printing_service
        self.location_service = location_service
        self.parser: CliArgumentParser = CliArgumentParser(description=self.description)
        self.setup_parser()
        self.setup_completer()

    def handle_command(self, *args):
        raise NotImplementedError

    def get_custom_completions(self, words, document: Document):
        raise NotImplementedError

    def setup_params(self):
        raise NotImplementedError

    def setup_parser(self):
        raise NotImplementedError

    def arg_is_multi_word(self, arg_name):
        raise NotImplementedError

    def find_last_flag(self, words):
        for word in reversed(words):
            if word.startswith(FLAG):
                return word
        return None

    def setup_completer(self):
        self.positional_completer = WordCompleter(self.parser.positional_args, ignore_case=True)
        self.flagged_completer = WordCompleter(self.parser.flag_args, ignore_case=True, match_middle=True)

    def get_completions(self, document: Document, complete_event):
        try:
            text = document.text_before_cursor
            words = text.split(" ")[1:]
            logger.debug(f"generic autocomplete: {words}")
            word_count = len(words)
            flag_count = len([s for s in words if s.startswith(FLAG)])
            last_flag = self.find_last_flag(words)
            if word_count <= len([param for param in self.mandatory_params if not param.startswith(FLAG)]):
                for completion in self.positional_completer.get_completions(document, complete_event):
                    yield Completion(completion.text, start_position=-len(document.get_word_before_cursor()))
            elif (words[-1] == "" and not words[-2].startswith(FLAG) and not self.arg_is_multi_word(last_flag)) or words[-1].startswith(FLAG):
                for completion in [completion for completion in self.flagged_completer.get_completions(document, complete_event) if
                                   completion.text not in words and (completion.text in self.mandatory_params or flag_count >= len(self.mandatory_params))]:
                    if words[-1] == "":
                        start_position = -len(document.get_word_before_cursor())
                    else:
                        text_before_cursor = document.text_before_cursor
                        hyphen_index = text_before_cursor.rfind(FLAG)
                        start_position = hyphen_index - len(text_before_cursor)
                    yield Completion(completion.text, start_position=start_position)
            else:
                yield from self.get_custom_completions(words, document)
        except argparse.ArgumentError as e:
            raise e.with_traceback(None)

    def preprocess_input(self, user_input):
        words = []
        temp_word = []
        flag = None
        positional_done = False

        for word in user_input:
            if word.startswith('-') and len(word) > 1:
                if temp_word:
                    if flag:
                        words.append(flag)
                        words.append(" ".join(temp_word))
                    else:
                        words.extend(temp_word)
                    temp_word = []
                flag = word
                positional_done = True
            else:
                if positional_done:
                    temp_word.append(word)
                else:
                    words.append(word)

        if temp_word:
            if flag:
                words.append(flag)
                words.append(" ".join(temp_word))
            else:
                words.extend(temp_word)

        return words

    def parse_input(self, args):
        return self.parser.parse_args(args)

    def arg_name(self, arg) -> str:
        return f"{FLAG}{arg}"

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


class MultiWordArgumentCommand(Command, ABC):
    pass

    def get_custom_completions(self, words, document: Document):
        logger.debug(f"custom autocomplete: {self.preprocess_input(words)}")
        user_input = self.parse_input(self.preprocess_input(words))

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

        yield from self.get_suggestions(user_input, start_position, words[last_flag_index])

    def get_suggestions(self, user_input, start_position, flag):
        raise NotImplementedError


class RegionScopedCommand(MultiWordArgumentCommand, ABC):
    pass

    scope_arg = "scope"
    region_arg = "region"
    back_arg = "back"
    days_back = [str(num) for num in list(range(1, 31))]

    def handle_command(self, *args):
        processed_input = self.preprocess_input(' '.join(args).split())
        logger.debug(f"user input: {processed_input}")
        user_input = self.parse_input(processed_input)
        days_back = 7
        if user_input.back:
            days_back = int(user_input.back)

        self.handle_observations(user_input.region, user_input.scope, days_back)

    def get_suggestions(self, user_input, start_position, flag):
        if flag == self.arg_name(self.region_arg):
            for completion in self.get_region_suggestions(user_input.scope, user_input.region):
                yield Completion(completion, start_position=start_position)
        else:
            for completion in [day for day in self.days_back if user_input.back in day]:
                yield Completion(completion, start_position=start_position)

    def get_region_suggestions(self, scope, region) -> list:
        if scope == RegionalScopes.PROVINCIAL.value:
            return self.location_service.get_subnationals()
        elif scope == RegionalScopes.REGIONAL.value:
            return self.location_service.get_regions() if region == "" else self.location_service.search_regions(region)
        elif scope == RegionalScopes.HOTSPOT.value:
            return self.location_service.get_hotspots() if region == "" else self.location_service.search_hotspots(region)
        else:
            return []

    def setup_params(self):
        self.mandatory_params = [self.scope_arg, self.arg_name(self.region_arg)]
        self.optional_params = [self.arg_name(self.back_arg)]

    def setup_parser(self):
        self.parser.add_positional_argument(self.scope_arg, type=str, choices=[scope.value for scope in RegionalScopes], help='Regional scope')
        self.parser.add_flag_argument(self.arg_name(self.region_arg), type=str, required=True, help='Region code')
        self.parser.add_flag_argument(self.arg_name(self.back_arg), type=str, required=False, help="Days to search back")

    def arg_is_multi_word(self, arg_name):
        return arg_name == self.arg_name(self.region_arg)

    def get_regions(self, region, scope):
        regions = []
        if scope == RegionalScopes.PROVINCIAL.value:
            regions = self.location_service.get_subnational_id(region)
        elif scope == RegionalScopes.REGIONAL.value:
            regions = self.location_service.get_region_id(region)
        elif scope == RegionalScopes.HOTSPOT.value:
            regions = self.location_service.get_hotspot_ids(region)

        return regions

    def handle_observations(self, region, scope, back):
        raise NotImplementedError


class RecentCommand(RegionScopedCommand):
    command_name = "recent"
    description = "Retrieve recent observations for the specified region"

    def handle_observations(self, region, scope, back):
        regions = self.get_regions(region, scope)
        logger.debug(f"regions to fetch: {regions}")
        self.printing_service.print_recent(self.observation_service.get_unique_recent_observations(regions, back))


class NotableCommand(RegionScopedCommand):
    command_name = "notable"
    description = "Retrieve notable observations for the specified region"

    def handle_observations(self, region, scope, back):
        regions = self.get_regions(region, scope)
        logger.debug(f"regions to fetch: {regions}")
        self.printing_service.print_notable(self.observation_service.get_notable_observations(regions, back))
