from abc import ABC, abstractmethod
from collections.abc import Generator
from enum import Enum

from prompt_toolkit.completion import Completion

from ..domain.regional_scopes import RegionalScopes
from ..services import LocationCatalogue, TaxonomyService
from .argument_parser import CliArgumentParser
from .input_processing import FLAG, flag_arg_name


class ArgumentNames(Enum):
    SCOPE = "scope"
    REGION = "region"
    BACK = "back"
    SPECIES = "species"


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

    def get_excluded_flags(self, _words) -> list:
        return []


class RegionScopeArgument(CommandArgument):
    scope_arg = str(ArgumentNames.SCOPE.value)
    region_arg = str(ArgumentNames.REGION.value)

    def __init__(self, location_catalogue: LocationCatalogue):
        self.location_catalogue = location_catalogue

    def get_flag_values(self, user_input, start_position) -> Generator:
        for completion in self.get_region_completions(RegionalScopes(user_input.scope), user_input.region):
            yield Completion(completion, start_position=start_position)

    def setup_parser(self, parser: CliArgumentParser):
        parser.add_positional_argument(
            self.scope_arg,
            type=str,
            choices=[scope.value for scope in RegionalScopes],
            help="Regional scope",
        )
        parser.add_flag_argument(flag_arg_name(self.region_arg), type=str, required=False, help="Region code")

    def get_mandatory_arguments(self):
        return [self.scope_arg]

    def get_optional_arguments(self):
        return [flag_arg_name(self.region_arg)]

    def arg_is_multi_word(self, arg_name: str):
        return arg_name == flag_arg_name(self.region_arg)

    def get_keywords(self, user_input):
        return {self.scope_arg: RegionalScopes(user_input.scope), self.region_arg: user_input.region}

    def supports_flag_argument_completion(self, arg_name: str):
        return arg_name == flag_arg_name(self.region_arg)

    def get_excluded_flags(self, words) -> list:
        positional_words = [w for w in words if not w.startswith(FLAG)]
        if positional_words and positional_words[0] == RegionalScopes.NEARBY:
            return [flag_arg_name(self.region_arg)]
        return []

    def get_region_completions(self, scope: RegionalScopes, region: str | None) -> list:
        return self.location_catalogue.names(scope, region or "")


class BackArgument(CommandArgument):
    back_arg = str(ArgumentNames.BACK.value)
    min_days_back = 1
    max_days_back = 30
    default_days_back = "7"
    days_back = [str(num) for num in range(min_days_back, max_days_back + 1)]

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
        return {self.back_arg: user_input.back if self.is_valid_days_back(user_input.back) else self.default_days_back}

    def is_valid_days_back(self, back: str | None) -> bool:
        try:
            return self.min_days_back <= int(back) <= self.max_days_back
        except (TypeError, ValueError):
            return False

    def supports_flag_argument_completion(self, arg_name: str):
        return arg_name == flag_arg_name(self.back_arg)


class SpeciesArgument(CommandArgument):
    species_arg = str(ArgumentNames.SPECIES.value)

    def __init__(self, taxonomy_service: TaxonomyService):
        self.taxonomy_service = taxonomy_service

    def get_flag_values(self, user_input, start_position) -> Generator:
        name = user_input.species or ""
        completions = self.taxonomy_service.search_by_common_name(name) if name else []
        for completion in completions:
            yield Completion(completion, start_position=start_position)

    def setup_parser(self, parser: CliArgumentParser):
        parser.add_flag_argument(flag_arg_name(self.species_arg), type=str, required=False, help="Species common name")

    def get_mandatory_arguments(self):
        return []

    def get_optional_arguments(self):
        return [flag_arg_name(self.species_arg)]

    def arg_is_multi_word(self, arg_name: str):
        return arg_name == flag_arg_name(self.species_arg)

    def get_keywords(self, user_input):
        return {self.species_arg: user_input.species}

    def supports_flag_argument_completion(self, arg_name: str):
        return arg_name == flag_arg_name(self.species_arg)
