from .dataframe import DataFrameService
from ..domain.fields import EbirdFields
from ..domain.taxonomy_cache import TaxonomyCache


class TaxonomyService(DataFrameService):
    def __init__(self, taxonomy_cache: TaxonomyCache):
        self.taxonomy_cache = taxonomy_cache

    def search_by_common_name(self, name: str) -> list[str]:
        df = self.taxonomy_cache.national
        matches = df[df[EbirdFields.common_name].str.contains(name, na=False, case=False)]
        return matches[EbirdFields.common_name].to_list()

    def get_species_code(self, common_name: str) -> list[str]:
        df = self.taxonomy_cache.national
        matches = df[df[EbirdFields.common_name] == common_name]
        return matches[EbirdFields.species_code].to_list()
