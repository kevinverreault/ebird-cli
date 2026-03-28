import csv
import os
import pandas as pd
import requests
from ebird.api import Client
from appdirs import user_cache_dir
from ..domain.location_cache import LocationCache
from ..domain.taxonomy_cache import TaxonomyCache
from ..domain.region import Region
from ..domain.fields import EbirdFields

CACHE_DIR = user_cache_dir("ebird_cli")
LOCATION_DIR = "location"
TAXONOMY_DIR = "taxonomy"

os.makedirs(CACHE_DIR, exist_ok=True)


class CacheService:
    def __init__(self, api_key: str, locale: str, region: Region):
        self.api_client = Client(api_key, locale)
        print(locale)
        self.api_client.detail = "full"

        os.makedirs(CACHE_DIR, exist_ok=True)
        os.makedirs(
            os.path.join(CACHE_DIR, LOCATION_DIR, region.national), exist_ok=True
        )
        os.makedirs(
            os.path.join(CACHE_DIR, LOCATION_DIR, region.national, region.subnational),
            exist_ok=True,
        )

        national_subregions_path = os.path.join(
            CACHE_DIR, LOCATION_DIR, region.national, "subregions.csv"
        )
        subnational_subregions_path = os.path.join(
            CACHE_DIR,
            LOCATION_DIR,
            region.national,
            region.subnational,
            "subregions.csv",
        )
        subnational_hotspots_path = os.path.join(
            CACHE_DIR, LOCATION_DIR, region.national, region.subnational, "hotspots.csv"
        )

        if not os.path.exists(national_subregions_path):
            subnationals = self.api_client.get_regions("subnational1", region.national)
            self.write_csv(national_subregions_path, subnationals)

        if not os.path.exists(subnational_subregions_path):
            subregionals = self.api_client.get_regions(
                "subnational2", region.subnational
            )
            hotspots = self.api_client.get_hotspots(region.subnational)
            self.write_csv(subnational_subregions_path, subregionals)
            self.write_csv(subnational_hotspots_path, hotspots)

        national_taxonomy_path = self.get_taxonomy(api_key, locale, region)

        self.taxonomy_cache = TaxonomyCache(region, national_taxonomy_path)
        self.location_cache = LocationCache(
            region,
            national_subregions_path,
            subnational_subregions_path,
            subnational_hotspots_path,
        )

    def write_csv(self, file_path, data):
        with open(file_path, mode="w", newline="", encoding="utf-8") as csvfile:
            fieldnames = list(dict.fromkeys(k for row in data for k in row.keys()))
            writer = csv.DictWriter(
                csvfile,
                fieldnames=fieldnames,
                quoting=csv.QUOTE_MINIMAL,
                extrasaction="ignore",
            )

            writer.writeheader()
            writer.writerows(data)

    def get_taxonomy(self, api_key: str, locale: str, region: Region) -> str:
        taxonomy_path = os.path.join(CACHE_DIR, TAXONOMY_DIR, "taxonomy.csv")
        national_taxonomy_path = os.path.join(
            CACHE_DIR, TAXONOMY_DIR, region.national, "taxonomy.csv"
        )

        if not os.path.exists(taxonomy_path):
            taxonomy = self.fetch_taxonomy(api_key, locale)
            os.makedirs(os.path.dirname(taxonomy_path), exist_ok=True)
            self.write_csv(taxonomy_path, taxonomy)

        taxonomy_df = pd.read_csv(taxonomy_path)

        if not os.path.exists(national_taxonomy_path):
            national_species = self.get_national_species(api_key, region)
            national_taxonomy_df = taxonomy_df[
                taxonomy_df[EbirdFields.species_code].isin(national_species)
            ]
            os.makedirs(os.path.dirname(national_taxonomy_path), exist_ok=True)
            national_taxonomy_df.to_csv(national_taxonomy_path, index=False)

        return national_taxonomy_path

    def fetch_taxonomy(self, api_key: str, locale: str) -> list[dict]:
        url = "https://api.ebird.org/v2/ref/taxonomy/ebird"
        headers = {"X-eBirdApiToken": api_key}
        params = {"fmt": "json", "locale": locale}
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()

    def get_national_species(self, api_key: str, region: Region) -> list[str]:
        url = f"https://api.ebird.org/v2/product/spplist/{region.national}"
        headers = {"X-eBirdApiToken": api_key}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
