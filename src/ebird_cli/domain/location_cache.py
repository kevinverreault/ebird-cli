import pandas
from ..domain.region import Region


class LocationCache:
    def __init__(self, region: Region, subnationals: str, subregionals: str, hotspots: str):
        self.subnationals: pandas.DataFrame = pandas.read_csv(subnationals)
        self.subregionals: pandas.DataFrame = pandas.read_csv(subregionals)
        self.hotspots: pandas.DataFrame = pandas.read_csv(hotspots)
        self.region = region
