import csv
import os

import pandas as pd
from appdirs import user_cache_dir

from ..domain.fields import EbirdFields
from ..domain.region import Region
from ..domain.taxonomy_cache import TaxonomyCache
from .ebird_client import EbirdClient

TAXONOMY_DIR = "taxonomy"


def write_csv(file_path, data):
    with open(file_path, mode="w", newline="", encoding="utf-8") as csvfile:
        fieldnames = list(dict.fromkeys(k for row in data for k in row))
        writer = csv.DictWriter(
            csvfile,
            fieldnames=fieldnames,
            quoting=csv.QUOTE_MINIMAL,
            extrasaction="ignore",
        )

        writer.writeheader()
        writer.writerows(data)


class CacheService:
    def __init__(self, api_key: str, locale: str, region: Region, api_client=None, cache_dir: str | None = None):
        self.api_client = api_client or EbirdClient(api_key, locale)
        self.cache_dir = cache_dir or user_cache_dir("ebird_cli")

        national_taxonomy_path = self.get_taxonomy(region)

        self.taxonomy_cache = TaxonomyCache(region, national_taxonomy_path)

    def get_taxonomy(self, region: Region) -> str:
        taxonomy_path = os.path.join(self.cache_dir, TAXONOMY_DIR, "taxonomy.csv")
        national_taxonomy_path = os.path.join(self.cache_dir, TAXONOMY_DIR, region.national, "taxonomy.csv")

        if not os.path.exists(taxonomy_path):
            taxonomy = self.api_client.get_ebird_taxonomy()
            os.makedirs(os.path.dirname(taxonomy_path), exist_ok=True)
            write_csv(taxonomy_path, taxonomy)

        taxonomy_df = pd.read_csv(taxonomy_path)

        if not os.path.exists(national_taxonomy_path):
            national_species = self.api_client.get_national_species(region.national)
            national_taxonomy_df = taxonomy_df[taxonomy_df[EbirdFields.species_code].isin(national_species)]
            os.makedirs(os.path.dirname(national_taxonomy_path), exist_ok=True)
            national_taxonomy_df.to_csv(national_taxonomy_path, index=False)

        return national_taxonomy_path
