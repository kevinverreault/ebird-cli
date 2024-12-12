import pandas

from ..domain.fields import ExportFields


class DataFrameService:
    def is_csv(self, filename) -> bool:
        return filename[-3:] == "csv"

    def get_dataframe(self, filepath) -> pandas.DataFrame:
        if filepath and self.is_csv(filepath):
            return pandas.read_csv(filepath)
        else:
            return pandas.DataFrame(columns=[ExportFields.common_name])
