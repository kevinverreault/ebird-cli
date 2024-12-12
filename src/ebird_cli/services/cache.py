import csv
import os
from ebird.api import Client
from appdirs import user_cache_dir
from ..domain.location_cache import LocationCache
from ..domain.region import Region

CACHE_DIR = user_cache_dir("ebird_cli")
LOCATION_DIR = "location"

os.makedirs(CACHE_DIR, exist_ok=True)


class CacheService:
    def __init__(self, api_key: str, locale: str, region: Region):
        self.api_client = Client(api_key, locale)
        self.api_client.detail = 'full'

        os.makedirs(CACHE_DIR, exist_ok=True)
        os.makedirs(os.path.join(CACHE_DIR, LOCATION_DIR, region.national), exist_ok=True)
        os.makedirs(os.path.join(CACHE_DIR, LOCATION_DIR, region.national, region.subnational), exist_ok=True)

        national_subregions_path = os.path.join(CACHE_DIR, LOCATION_DIR, region.national, "subregions.csv")
        subnational_subregions_path = os.path.join(CACHE_DIR, LOCATION_DIR, region.national, region.subnational, "subregions.csv")
        subnational_hotspots_path = os.path.join(CACHE_DIR, LOCATION_DIR, region.national, region.subnational, "hotspots.csv")

        if not os.path.exists(national_subregions_path):
            subnationals = self.api_client.get_regions('subnational1', region.national)
            self.write_csv(national_subregions_path, subnationals)

        if not os.path.exists(subnational_subregions_path):
            subregionals = self.api_client.get_regions('subnational2', region.subnational)
            hotspots = self.api_client.get_hotspots(region.subnational)
            self.write_csv(subnational_subregions_path, subregionals)
            self.write_csv(subnational_hotspots_path, hotspots)

        self.location_cache = LocationCache(region, national_subregions_path, subnational_subregions_path, subnational_hotspots_path)

    def write_csv(self, file_path, data):
        with open(file_path, mode='w', newline='', encoding='utf-8') as csvfile:
            fieldnames = data[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)

            writer.writeheader()
            writer.writerows(data)
