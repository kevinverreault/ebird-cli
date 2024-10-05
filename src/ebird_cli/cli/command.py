from colorama import Fore
from ..services.location import LocationService
from ..services.observation import ObservationService
from ..services.printing import PrintingService


class Command:
    command_name = None
    mandatory_params = []
    optional_params = []
    description = None

    def __init__(self, observation_service: ObservationService, printing_service: PrintingService, location_service: LocationService):
        self.observation_service = observation_service
        self.printing_service = printing_service
        self.location_service = location_service

    def handle_command(self, *args):
        raise NotImplementedError

    def get_completions(self, words):
        raise NotImplementedError

    def single_param_command(self) -> bool:
        raise NotImplementedError

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
        mandatory_params = f"{Fore.MAGENTA}<{' '.join(self.mandatory_params)}>{Fore.RESET}" if len(self.mandatory_params) else ""
        optional_params = f"{Fore.CYAN}[{' '.join(self.optional_params)}]{Fore.RESET}" if len(self.optional_params) > 0 else ""

        return f"{command_name:18} {mandatory_params} {optional_params}"


class ConfigureCommand(Command):
    command_name = "configure"
    mandatory_params = ["key", "value"]
    description = "Configure CLI parameters"
    parameters = ["location", "back"]

    def handle_command(self, *args):
        if len(args) > 2:
            key = args[0]
            if key == self.parameters[0]:
                self.location_service.set_location(' '.join(map(str, args[1:])))
            elif key == self.parameters[1]:
                if self.validate_days(args[1]):
                    self.observation_service.set_range_in_days(args[1])
        else:
            self.print_description()
            self.print_mandatory_param(self.mandatory_params[0], f"CLI parameters to configure: {self.parameters}")
            self.print_mandatory_param(self.mandatory_params[1], f"Value of CLI parameter")

    def get_completions(self, words):
        if len(words) >= 3:
            key = words[1]
            value = words[2]
            if key == self.parameters[0]:
                return self.location_service.search_subregions(value)
            elif key == self.parameters[1]:
                return [str(x) for x in range(1, 31)]
            else:
                return []
        elif len(words) == 2:
            return [x for x in ["location", "back"] if words[1] in x]
        else:
            return []

    def single_param_command(self) -> bool:
        return False

    def change_location(self, location_id):
        self.location_service.set_location(location_id)

    def validate_days(self, days):
        if 0 < int(days) <= 31:
            return True
        else:
            print("Error: 'days' should be between 1 and 30.")
            return False


class RecentCommand(Command):
    command_name = "recent"
    mandatory_params = ["location"]
    optional_params = []
    description = "Retrieve recent observations for the specified location"

    def handle_command(self, *args):
        if len(args) > 0:
            location = ' '.join(map(str, args))
            self.recent(location)
        elif len(args) == 0:
            self.print_description()
            self.print_mandatory_param("location", f"Location name of eBird hotspot.")
        else:
            print("Invalid number of arguments for 'recent'.")

    def get_completions(self, words):
        if len(words) > 1:
            location_name = " ".join(words[1:])
            return self.location_service.search_hotspots(location_name)
        elif len(words) == 1:
            return self.location_service.get_hotspots()
        return []

    def single_param_command(self) -> bool:
        return True

    def recent(self, location):
        if not self.location_service.hotspot_exists(location):
            print(f"{location} not found")
        else:
            self.printing_service.print_recent(self.observation_service.get_unique_recent_observations(self.location_service.get_hotspot_ids(location)))


class NotableCommand(Command):
    command_name = "notable"
    mandatory_params = ["region"]
    description = "Retrieve recent observations for the specified location"

    def handle_command(self, *args):
        if len(args) == 1:
            region = args[0]
            self.notable(region)
        elif len(args) == 0:
            self.all_notable()
        else:
            print("Invalid number of arguments for 'recent'.")

    def get_completions(self, words):
        if len(words) == 2:
            current_input = words[1]
            return self.location_service.search_subregions(current_input)
        elif len(words) == 1:
            return self.location_service.get_subregions()
        return []

    def single_param_command(self) -> bool:
        return True

    def notable(self, region):
        location_id = self.location_service.get_subregion_id(region)
        self.printing_service.print_notable(self.observation_service.get_notable_observations(location_id))

    def all_notable(self):
        self.printing_service.print_notable(self.observation_service.get_notable_observations(self.location_service.subnational))

