import json
import os
from .dataframe import DataFrameService
from ..domain.fields import EbirdFields

FAVORITES_FILE = "~/ebird_data/favorites.json"


class LocationService(DataFrameService):
    def __init__(self, default_region):

        fav_file = os.path.expanduser(FAVORITES_FILE)
        if os.path.isfile(fav_file):
            with open(fav_file, "r", encoding="utf-8") as file:
                favorites = json.load(file)
                self.favorites = {}
                for favorite in favorites:
                    self.favorites.update(favorite)
        else:
            self.favorites = None

        with open(os.path.join(os.path.dirname(__file__), "../data/ca-qc_hotspots.json"), 'r', encoding='utf-8') as file:
            hotspots_json = json.load(file)
        self.hotspots = {entry["locId"]: entry for entry in hotspots_json}

        with open(os.path.join(os.path.dirname(__file__), "../data/ca-qc_subregions.json"), 'r', encoding='utf-8') as file:
            subregions_json = json.load(file)
        self.regions = {entry['name']: entry['code'] for entry in subregions_json}

        self.current_location = next((key for key, value in self.regions.items() if value == default_region), None)
        self.subnationals = {"Québec": default_region[:5]}

    def get_subnationals(self) -> list:
        return [key for key, value in self.subnationals.items()]

    def get_subnational_id(self, subnational_name):
        return [value for key, value in self.subnationals.items() if subnational_name == key]

    def get_regions(self) -> list:
        return list(self.regions.keys())

    def search_regions(self, region_name: str) -> list:
        return [key for key in self.regions.keys() if region_name.lower() in key.lower()]

    def get_region_id(self, region_name: str) -> list:
        return [value for key, value in self.regions.items() if region_name == key]

    def set_location(self, current_location):
        self.current_location = current_location

    def get_hotspots(self) -> list:
        return [value[EbirdFields.location_name] for value in self.hotspots.values() if EbirdFields.location_name in value] + self.get_favorites()

    def hotspot_exists(self, hotspot_name: str) -> bool:
        return any(
            EbirdFields.location_name in value and
            (hotspot_name == value[EbirdFields.location_name] or hotspot_name in self.favorites)
            # and self.subregions[self.current_location] in value[EbirdFields.sub_subnational_code]
            for key, value in self.hotspots.items()
        )

    def get_hotspot_ids(self, hotspot_name: str) -> list:
        return [value[EbirdFields.location_id] for key, value in self.hotspots.items() if
                EbirdFields.location_name in value and hotspot_name == value[EbirdFields.location_name]] + [value for key, value in self.favorites.items() if hotspot_name == key]

    def search_hotspots(self, hotspot_name: str) -> list:
        return [value[EbirdFields.location_name] for key, value in self.hotspots.items() if
                EbirdFields.location_name in value and hotspot_name.lower() in value[EbirdFields.location_name].lower()] + self.search_favorites(hotspot_name)
        # and self.subregions[self.current_location] in value[EbirdFields.sub_subnational_code]]

    def get_favorites(self) -> list:
        return [*self.favorites] if self.favorites else []

    def search_favorites(self, favorite_name: str) -> list:
        if not self.favorites:
            return []

        return [key for key, value in self.favorites.items() if favorite_name.lower() in key.lower()]
