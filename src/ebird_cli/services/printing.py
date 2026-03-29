from .dataframe import DataFrameService
from ..domain.fields import ExportFields
from rich.console import Console, Text
from rich.table import Table


class PrintingService(DataFrameService):
    def __init__(self, life_list: str | None, year_list: str | None):
        self.life_list = self.get_dataframe(life_list) if life_list else None
        self.year_list = self.get_dataframe(year_list) if year_list else None
        self.console = Console()

    def print_notable(self, notable_observations: list):
        self.print_observations(notable_observations, lambda obs: obs.location)

    def print_recent(self, recent_observations: list):
        self.print_observations(recent_observations, lambda obs: obs.location)

    def print_observations(self, observations, location):
        table = Table()

        table.add_column('Date', style='magenta')
        table.add_column('Observation')
        table.add_column('Location')

        regions = {obs.subname for obs in observations}
        show_region = len(regions) > 1

        if show_region:
            table.add_column('Region')

        for observation in observations:
            row = (observation.observation_date, self.get_observation_text(observation), location(observation))
            if show_region:
                row += (observation.subname,)
            table.add_row(*row)

        print()
        self.console.print(table)
        print()
        print(f"Total: {len(observations)}")

    def get_observation_text(self, observation):
        is_year_target = False
        is_life_target = False
        if self.year_list is not None:
            is_year_target = not (self.year_list[ExportFields.common_name] == observation.name).any()
        if self.life_list is not None:
            is_life_target = not (self.life_list[ExportFields.common_name] == observation.name).any()

        if is_life_target:
            style = 'red'
        elif is_year_target:
            style = 'green'
        else:
            style = 'white'

        return Text(observation.name, style)

