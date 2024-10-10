from abc import ABC
from colorama import Fore
from .argument_parser import CliArgumentParser
from ..domain.regional_levels import RegionalLevels
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
            # words = self.preprocess_input(text.split(" ")[1:])
            words = text.split(" ")[1:]
            logger.debug(f"generic autocomplete: {words}")
            word_count = len(words)
            last_flag = self.find_last_flag(words)
            if word_count <= len([param for param in self.mandatory_params if not param.startswith(FLAG)]):
                for completion in self.positional_completer.get_completions(document, complete_event):
                    yield Completion(completion.text, start_position=-len(document.get_word_before_cursor()))
            elif (words[-1] == "" and not words[-2].startswith(FLAG) and not self.arg_is_multi_word(last_flag)) or words[-1].startswith(FLAG):
                for completion in self.flagged_completer.get_completions(document, complete_event):
                    if words[-1] == "":
                        start_position = -len(document.get_word_before_cursor())
                    else:
                        text_before_cursor = document.text_before_cursor
                        hyphen_index = text_before_cursor.rfind("-")
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


# class ConfigureCommand(Command):
#     command_name = "configure"
#     mandatory_params = ["key", "value"]
#     description = "Configure CLI parameters"
#     parameters = ["location", "back"]
#
#     def handle_command(self, *args):
#         if len(args) >= 2:
#             key = args[0]
#             if key == self.parameters[0]:
#                 self.location_service.set_location(' '.join(map(str, args[1:])))
#             elif key == self.parameters[1]:
#                 if self.validate_days(args[1]):
#                     self.observation_service.set_range_in_days(args[1])
#         else:
#             self.print_description()
#             self.print_mandatory_param(self.mandatory_params[0], f"CLI parameters to configure: {self.parameters}")
#             self.print_mandatory_param(self.mandatory_params[1], f"Value of CLI parameter")
#
#     def get_completions(self, words):
#         if len(words) >= 3:
#             key = words[1]
#             value = words[2]
#             if key == self.parameters[0]:
#                 return self.location_service.search_subregions(value)
#             elif key == self.parameters[1]:
#                 return [str(x) for x in range(1, 31)]
#             else:
#                 return []
#         elif len(words) == 2:
#             return [x for x in ["location", "back"] if words[1] in x]
#         else:
#             return []
#
#     def single_param_command(self) -> bool:
#         return False
#
#     def change_location(self, location_id):
#         self.location_service.set_location(location_id)
#
#     def validate_days(self, days):
#         if 0 < int(days) <= 31:
#             return True
#         else:
#             print("Error: 'days' should be between 1 and 30.")
#             return False

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

        for completion in self.get_suggestions(user_input):
            yield Completion(completion, start_position=start_position)

    def get_suggestions(self, user_input):
        raise NotImplementedError


class RegionLevelCommand(MultiWordArgumentCommand, ABC):
    pass

    level_arg = "level"
    region_arg = "region"
    back_arg = "back"

    def handle_command(self, *args):
        processed_input = self.preprocess_input(' '.join(args).split())
        logger.debug(f"user input: {processed_input}")
        user_input = self.parse_input(processed_input)

        if user_input.level and user_input.region:
            self.handle_observations(user_input.region, user_input.level)
        else:
            print(f"{self.mandatory_params} are required.")

    def get_suggestions(self, user_input):
        level = user_input.level
        region = user_input.region
        if level == RegionalLevels.PROVINCIAL.value:
            return self.location_service.get_subnationals()
        elif level == RegionalLevels.REGIONAL.value:
            return self.location_service.get_regions() if region == "" else self.location_service.search_regions(region)
        elif level == RegionalLevels.LOCATION.value:
            return self.location_service.get_hotspots() if region == "" else self.location_service.search_hotspots(region)
        else:
            return []

    def setup_params(self):
        self.mandatory_params = [self.level_arg, self.arg_name(self.region_arg)]

    def setup_parser(self):
        self.parser.add_positional_argument('level', type=str, choices=[level.value for level in RegionalLevels], help='Regional level')
        self.parser.add_flag_argument('-region', type=str, required=True, help='Region code')

    def arg_is_multi_word(self, arg_name):
        return arg_name == self.arg_name(self.region_arg)

    def get_regions(self, region, level):
        regions = []
        if level == RegionalLevels.PROVINCIAL.value:
            regions = self.location_service.get_subnational_id(region)
        elif level == RegionalLevels.REGIONAL.value:
            regions = self.location_service.get_region_id(region)
        elif level == RegionalLevels.LOCATION.value:
            regions = self.location_service.get_hotspot_ids(region)

        return regions

    def handle_observations(self, region, level):
        raise NotImplementedError


class RecentCommand(RegionLevelCommand):
    command_name = "recent"
    description = "Retrieve recent observations for the specified region"

    def handle_observations(self, region, level):
        regions = self.get_regions(region, level)
        logger.debug(f"regions to fetch: {regions}")
        self.printing_service.print_recent(self.observation_service.get_unique_recent_observations(regions))


class NotableCommand(RegionLevelCommand):
    command_name = "notable"
    description = "Retrieve notable observations for the specified region"

    def handle_observations(self, region, level):
        regions = self.get_regions(region, level)
        logger.debug(f"regions to fetch: {regions}")
        self.printing_service.print_notable(self.observation_service.get_notable_observations(regions))
