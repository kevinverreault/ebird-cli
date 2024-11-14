from colorama import Fore

from .dataframe import DataFrameService
from ..domain.fields import ExportFields


class PrintingService(DataFrameService):
    def __init__(self, life_list: str or None, year_list: str or None):
        self.life_list = self.get_dataframe(life_list) if life_list else None
        self.year_list = self.get_dataframe(year_list) if year_list else None

    def is_csv(self, filename) -> bool:
        return filename[-3:] == "csv"

    def print_notable(self, notable_observations: list):
        print()
        for obs in notable_observations:
            a = f"{obs.name[0:32]:32}"
            obs_text = f"{a} ({obs.observation_date:10}) | {obs.location[0:45]:45} | {obs.subname:28}"
            print(self.get_text_color(obs) + obs_text + Fore.RESET)
        print()
        print(f"Total: {len(notable_observations)}")

    def print_recent(self, recent_observations: list):
        print()
        for observation in recent_observations:
            obs_text = f"{observation.name:28} ({observation.observation_date:10}) | {observation.location:48}"
            print(self.get_text_color(observation) + obs_text + Fore.RESET)
        print()
        print(f"Total: {len(recent_observations)}")

    def get_text_color(self, observation):
        is_year_target = False
        is_life_target = False
        if self.year_list is not None:
            is_year_target = not (self.year_list[ExportFields.common_name] == observation.name).any()
        if self.life_list is not None:
            is_life_target = not (self.life_list[ExportFields.common_name] == observation.name).any()

        if is_life_target:
            text_color = Fore.RED
        elif is_year_target:
            text_color = Fore.GREEN
        else:
            text_color = Fore.WHITE

        return text_color
