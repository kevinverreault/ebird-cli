from rich.console import Console, Text
from rich.table import Table

from ..domain.fields import ExportFields
from ..domain.match import contains, spans
from .dataframe import DataFrameService


class PrintingService(DataFrameService):
    def __init__(self, life_list: str | None, year_list: str | None, console: Console | None = None):
        self.life_list = self.get_dataframe(life_list) if life_list else None
        self.year_list = self.get_dataframe(year_list) if year_list else None
        self.console = console or Console()
        self.last_result: list | None = None

    def print_observations(self, observations: list):
        """Print observations and keep them as the Last result."""
        self.last_result = observations
        self.print_table(observations, self.shows_region(observations))
        print(f"Total: {len(observations)}")

    def print_matches(self, text: str):
        """Print the Matches of text in the Last result, in the Last result's columns; no text reprints it whole."""
        if self.last_result is None:
            print("No observations to search yet; run recent or notable first.")
            return
        if not text:
            self.print_observations(self.last_result)
            return
        matches = [
            observation
            for observation in self.last_result
            if any(contains(value, text) for value in (observation.name, observation.location, observation.subname))
        ]
        if not matches:
            print(f'No observations match "{text}".')
            return
        self.print_table(matches, self.shows_region(self.last_result), text)
        print(f"Total: {len(matches)} of {len(self.last_result)}")

    @staticmethod
    def shows_region(observations: list) -> bool:
        return len({obs.subname for obs in observations}) > 1

    def print_table(self, observations: list, show_region: bool, text: str = ""):
        """Print the observations, with each occurrence of text in reverse video."""
        table = Table()

        table.add_column("Date", style="magenta")
        table.add_column("Observation")
        table.add_column("Location")

        if show_region:
            table.add_column("Region")

        for observation in observations:
            row = (
                observation.observation_date,
                highlight(self.get_observation_text(observation), text),
                highlight(Text(observation.location), text),
            )
            if show_region:
                row += (highlight(Text(observation.subname), text),)
            table.add_row(*row)

        print()
        self.console.print(table)
        print()

    def get_observation_text(self, observation):
        is_year_target = False
        is_life_target = False
        if self.year_list is not None:
            is_year_target = not (self.year_list[ExportFields.common_name] == observation.name).any()
        if self.life_list is not None:
            is_life_target = not (self.life_list[ExportFields.common_name] == observation.name).any()

        if is_life_target:
            style = "red"
        elif is_year_target:
            style = "green"
        else:
            style = "white"

        return Text(observation.name, style)


def highlight(shown: Text, text: str) -> Text:
    """Shown text with each occurrence of text in reverse video, which keeps its colour."""
    for start, end in spans(shown.plain, text):
        shown.stylize("reverse", start, end)
    return shown
