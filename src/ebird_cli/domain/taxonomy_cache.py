import pandas
from ..domain.region import Region


class TaxonomyCache:
    def __init__(self, region: Region, national_taxonomy: str):
        self.national: pandas.DataFrame = pandas.read_csv(national_taxonomy)
        self.region = region
