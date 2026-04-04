import json
import os
import pandas
from .dataframe import DataFrameService
from ..domain.fields import EbirdFields
from ..domain.regional_scopes import RegionalScopes
from ..domain.location_cache import LocationCache


class LocationService(DataFrameService):
    def __init__(self, location_cache: LocationCache, aggregations_file: str | None = None):
        self.default_regions = {}
        self.subnationals = {}
        self.location_cache = location_cache

        if aggregations_file:
            agg_file = os.path.expanduser(aggregations_file)
            if os.path.isfile(agg_file):
                with open(agg_file, "r", encoding="utf-8") as file:
                    aggregations = json.load(file)
                    self.aggregations = {}
                    for aggregation in aggregations:
                        self.aggregations.update(aggregation)
            else:
                self.aggregations = None
        else:
            self.aggregations = None

    def get_column(self, df: pandas.DataFrame, column: str):
        if not df.empty:
            return df[column].to_list()
        else:
            return []

    def search_by(self, df: pandas.DataFrame, column: str, value: str):
        return df[df[column].str.contains(value, na=False, case=False)]

    def get_by(self, df: pandas.DataFrame, column: str, value: str):
        return df[df[column] == value]

    def get_subnationals(self):
        return self.location_cache.subnationals[EbirdFields.name].to_list()

    def search_subnationals(self, region_name: str) -> list:
        return self.get_column(self.search_by(self.location_cache.subnationals, EbirdFields.name, region_name), EbirdFields.name)

    def get_subnational_id(self, subnational_name):
        return self.get_column(self.search_by(self.location_cache.subnationals, EbirdFields.name, subnational_name), EbirdFields.code)

    def get_regions(self) -> list:
        return self.location_cache.subregionals[EbirdFields.name].to_list()

    def search_regions(self, region_name: str) -> list:
        return self.get_column(self.search_by(self.location_cache.subregionals, EbirdFields.name, region_name), EbirdFields.name)

    def get_region_id(self, region_name: str) -> list:
        return self.get_column(self.search_by(self.location_cache.subregionals, EbirdFields.name, region_name), EbirdFields.code)

    def get_hotspots(self) -> list:
        return self.location_cache.hotspots[EbirdFields.location_name].to_list() + self.get_aggregations()

    def get_hotspot_ids(self, hotspot_name: str) -> list:
        hotspots = self.get_by(self.location_cache.hotspots, EbirdFields.location_name, hotspot_name)
        aggregation_ids = [id for key, ids in (self.aggregations or {}).items() if hotspot_name == key for id in ids]
        return self.get_column(hotspots, EbirdFields.location_id) + aggregation_ids

    def search_hotspots(self, hotspot_name: str) -> list:
        hotspots = self.search_by(self.location_cache.hotspots, EbirdFields.location_name, hotspot_name)
        return self.get_column(hotspots, EbirdFields.location_name) + self.search_aggregations(hotspot_name)

    def get_aggregations(self) -> list:
        return [*self.aggregations] if self.aggregations else []

    def search_aggregations(self, aggregation_name: str) -> list:
        if not self.aggregations:
            return []

        return [key for key, value in self.aggregations.items() if aggregation_name.lower() in key.lower()]

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
        return self.location_cache.region.subnational if scope == RegionalScopes.SUBNATIONAL.value else self.location_cache.region.regional
