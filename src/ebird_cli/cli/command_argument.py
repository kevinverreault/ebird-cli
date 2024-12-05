from enum import Enum
from typing import Generator
from abc import ABC, abstractmethod
from prompt_toolkit.completion import Completion
from .argument_parser import CliArgumentParser
from .input_processing import flag_arg_name
from ..domain.regional_scopes import RegionalScopes
from ..services import LocationService


class ArgumentNames(Enum):
    SCOPE = "scope"
    REGION = "region"
    BACK = "back"


class CommandArgument(ABC):
    @abstractmethod
    def get_flag_values(self, user_input, start_position) -> Generator:
        pass

    @abstractmethod
    def get_keywords(self, user_input):
        pass

    @abstractmethod
    def setup_parser(self, parser: CliArgumentParser):
        pass

    @abstractmethod
    def get_mandatory_arguments(self):
        pass

    @abstractmethod
    def get_optional_arguments(self):
        pass

    @abstractmethod
    def arg_is_multi_word(self, arg_name: str):
        pass

    @abstractmethod
    def supports_flag_argument_completion(self, arg_name: str):
        pass


class RegionScopeArgument(CommandArgument):
    scope_arg = str(ArgumentNames.SCOPE.value)
    region_arg = str(ArgumentNames.REGION.value)

    def __init__(self, location_service: LocationService):
        self.location_service = location_service

    def get_flag_values(self, user_input, start_position) -> Generator:
        for completion in self.get_region_completions(user_input.scope, user_input.region):
            yield Completion(completion, start_position=start_position)

    def setup_parser(self, parser: CliArgumentParser):
        parser.add_positional_argument(self.scope_arg, type=str, choices=[scope.value for scope in RegionalScopes], help='Regional scope')
        parser.add_flag_argument(flag_arg_name(self.region_arg), type=str, required=False, help='Region code')

    def get_mandatory_arguments(self):
        return [self.scope_arg, flag_arg_name(self.region_arg)]

    def get_optional_arguments(self):
        return []

    def arg_is_multi_word(self, arg_name: str):
        return arg_name == flag_arg_name(self.region_arg)

    def get_keywords(self, user_input):
        return {self.scope_arg: user_input.scope, self.region_arg: user_input.region}

    def supports_flag_argument_completion(self, arg_name: str):
        return arg_name == flag_arg_name(self.region_arg)

    def get_region_completions(self, scope, region) -> list:
        if scope == RegionalScopes.PROVINCIAL.value:
            return self.location_service.get_subnationals()
        elif scope == RegionalScopes.REGIONAL.value:
            return self.location_service.get_regions() if region == "" else self.location_service.search_regions(region)
        elif scope == RegionalScopes.HOTSPOT.value:
            return self.location_service.get_hotspots() if region == "" else self.location_service.search_hotspots(region)
        else:
            return []


class BackArgument(CommandArgument):
    back_arg = str(ArgumentNames.BACK.value)
    days_back = [str(num) for num in list(range(1, 30))]

    def get_flag_values(self, user_input, start_position) -> Generator:
        for completion in [day for day in self.days_back if user_input.back in day]:
            yield Completion(completion, start_position=start_position)

    def setup_parser(self, parser: CliArgumentParser):
        parser.add_flag_argument(flag_arg_name(self.back_arg), type=str, required=False, help="Days to search back")

    def get_mandatory_arguments(self):
        return []

    def get_optional_arguments(self):
        return [flag_arg_name(self.back_arg)]

    def arg_is_multi_word(self, arg_name: str):
        return False

    def get_keywords(self, user_input):
        return {self.back_arg: str(user_input.back) if user_input.back and 1 <= int(user_input.back) <= 30 else "7"}

    def supports_flag_argument_completion(self, arg_name: str):
        return arg_name == flag_arg_name(self.back_arg)
