import csv
import os

import pandas as pd
from appdirs import user_cache_dir

from ..domain.fields import EbirdFields
from ..domain.location_cache import LocationCache
from ..domain.region import Region
from ..domain.taxonomy_cache import TaxonomyCache
from .ebird_client import EbirdClient

LOCATION_DIR = "location"
TAXONOMY_DIR = "taxonomy"


class CacheService:
    def __init__(self, api_key: str, locale: str, region: Region, api_client=None, cache_dir: str | None = None):
        self.api_client = api_client or EbirdClient(api_key, locale)
        self.cache_dir = cache_dir or user_cache_dir("ebird_cli")

        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(os.path.join(self.cache_dir, LOCATION_DIR, region.national), exist_ok=True)
        os.makedirs(
            os.path.join(self.cache_dir, LOCATION_DIR, region.national, region.subnational),
            exist_ok=True,
        )

        national_subregions_path = os.path.join(self.cache_dir, LOCATION_DIR, region.national, "subregions.csv")
        subnational_subregions_path = os.path.join(
            self.cache_dir,
            LOCATION_DIR,
            region.national,
            region.subnational,
            "subregions.csv",
        )
        subnational_hotspots_path = os.path.join(
            self.cache_dir, LOCATION_DIR, region.national, region.subnational, "hotspots.csv"
        )

        if not os.path.exists(national_subregions_path):
            subnationals = self.api_client.get_regions("subnational1", region.national)
            self.write_csv(national_subregions_path, subnationals)

        if not os.path.exists(subnational_subregions_path):
            subregionals = self.api_client.get_regions("subnational2", region.subnational)
            hotspots = self.api_client.get_hotspots(region.subnational)
            self.write_csv(subnational_subregions_path, subregionals)
            self.write_csv(subnational_hotspots_path, hotspots)

        national_taxonomy_path = self.get_taxonomy(region)

        self.taxonomy_cache = TaxonomyCache(region, national_taxonomy_path)
        self.location_cache = LocationCache(
            region,
            national_subregions_path,
            subnational_subregions_path,
            subnational_hotspots_path,
        )

    def write_csv(self, file_path, data):
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

    def get_taxonomy(self, region: Region) -> str:
        taxonomy_path = os.path.join(self.cache_dir, TAXONOMY_DIR, "taxonomy.csv")
        national_taxonomy_path = os.path.join(self.cache_dir, TAXONOMY_DIR, region.national, "taxonomy.csv")

        if not os.path.exists(taxonomy_path):
            taxonomy = self.api_client.get_ebird_taxonomy()
            os.makedirs(os.path.dirname(taxonomy_path), exist_ok=True)
            self.write_csv(taxonomy_path, taxonomy)

        taxonomy_df = pd.read_csv(taxonomy_path)

        if not os.path.exists(national_taxonomy_path):
            national_species = self.api_client.get_national_species(region.national)
            national_taxonomy_df = taxonomy_df[taxonomy_df[EbirdFields.species_code].isin(national_species)]
            os.makedirs(os.path.dirname(national_taxonomy_path), exist_ok=True)
            national_taxonomy_df.to_csv(national_taxonomy_path, index=False)

        return national_taxonomy_path
