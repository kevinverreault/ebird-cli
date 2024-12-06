import json
import os
from enum import Enum

from .dataframe import DataFrameService
from ..domain.fields import EbirdFields
from ..domain.regional_scopes import RegionalScopes

FAVORITES_FILE = "~/ebird_data/favorites.json"


class RegionLevels(Enum):
    REGIONAL = "regional"
    SUBNATIONAL = "subnational"
    NATIONAL = "national"


class LocationService(DataFrameService):
    def __init__(self, default_region):
        self.default_regions = {}
        self.subnationals = {}

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

        self.set_default_region(default_region)

    def set_default_region(self, default_region: str):
        self.subnationals = {"Québec": default_region}
        region_segments = default_region.split('-')

        self.default_regions = {
            RegionLevels.NATIONAL.value: region_segments[0],
            RegionLevels.SUBNATIONAL.value: f"{region_segments[0]}-{region_segments[1]}",
            RegionLevels.REGIONAL.value: default_region
        }

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

    def get_hotspots(self) -> list:
        return [value[EbirdFields.location_name] for value in self.hotspots.values() if EbirdFields.location_name in value] + self.get_favorites()

    def hotspot_exists(self, hotspot_name: str) -> bool:
        return any(
            EbirdFields.location_name in value and
            (hotspot_name == value[EbirdFields.location_name] or hotspot_name in self.favorites)
            for key, value in self.hotspots.items()
        )

    def get_hotspot_ids(self, hotspot_name: str) -> list:
        return [value[EbirdFields.location_id] for key, value in self.hotspots.items() if
                EbirdFields.location_name in value and hotspot_name == value[EbirdFields.location_name]] + [value for key, value in self.favorites.items() if
                                                                                                            hotspot_name == key]

    def search_hotspots(self, hotspot_name: str) -> list:
        return [value[EbirdFields.location_name] for key, value in self.hotspots.items() if
                EbirdFields.location_name in value and hotspot_name.lower() in value[EbirdFields.location_name].lower()] + self.search_favorites(hotspot_name)

    def get_favorites(self) -> list:
        return [*self.favorites] if self.favorites else []

    def search_favorites(self, favorite_name: str) -> list:
        if not self.favorites:
            return []

        return [key for key, value in self.favorites.items() if favorite_name.lower() in key.lower()]

    def get_region_ids_by_scope(self, region_name: str | None, scope: RegionalScopes) -> list:
        regions = []
        if region_name is not None:
            if scope == RegionalScopes.SUBNATIONAL.value:
                regions = self.get_subnational_id(region_name)
            elif scope == RegionalScopes.REGIONAL.value:
                regions = self.get_region_id(region_name)
            elif scope == RegionalScopes.HOTSPOT.value:
                regions = self.get_hotspot_ids(region_name)
        else:
            regions.append(self.get_default_by_scope(scope))

        return regions

    def get_default_by_scope(self, scope: RegionalScopes):
        return self.default_regions[RegionLevels.SUBNATIONAL.value] if scope == RegionalScopes.SUBNATIONAL.value else self.default_regions[RegionLevels.REGIONAL.value]
