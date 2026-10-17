import json
import os
from collections.abc import Callable

from ..domain.fields import EbirdFields
from ..domain.region import Region
from ..domain.regional_scopes import RegionalScopes

LOCATION_DIR = "location"


def cached(file_path: str, fetch: Callable[[], list[dict]]) -> list[dict]:
    """The eBird response cached at file_path, fetched and stored verbatim first if it isn't there."""
    if not os.path.exists(file_path):
        response = fetch()
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(response, file, ensure_ascii=False, indent=2)
    with open(file_path, encoding="utf-8") as file:
        return json.load(file)


def read_aggregations(aggregations_path: str | None) -> dict[str, list[str]]:
    """Aggregation name to Hotspot ids, merged from every object in the file; a missing file means none."""
    if not aggregations_path:
        return {}
    file_path = os.path.expanduser(aggregations_path)
    if not os.path.isfile(file_path):
        return {}
    with open(file_path, encoding="utf-8") as file:
        aggregations = {}
        for aggregation in json.load(file):
            aggregations.update(aggregation)
        return aggregations


class LocationCatalogue:
    """Every Location the user can name around their Home Region, by Regional scope."""

    def __init__(
        self,
        home_region: Region,
        subnationals: list[dict],
        regionals: list[dict],
        hotspots: list[dict],
        aggregations: dict[str, list[str]],
    ):
        self.home_codes = {
            RegionalScopes.SUBNATIONAL: home_region.subnational,
            RegionalScopes.REGIONAL: home_region.regional,
            RegionalScopes.HOTSPOT: home_region.regional,
        }
        self.locations: dict[RegionalScopes, list[tuple[str, list[str]]]] = {
            RegionalScopes.SUBNATIONAL: [(row[EbirdFields.name], [row[EbirdFields.code]]) for row in subnationals],
            RegionalScopes.REGIONAL: [(row[EbirdFields.name], [row[EbirdFields.code]]) for row in regionals],
            RegionalScopes.HOTSPOT: [
                *((row[EbirdFields.location_name], [row[EbirdFields.location_id]]) for row in hotspots),
                *aggregations.items(),
            ],
        }

    @classmethod
    def load(cls, home_region: Region, client, cache_dir: str, aggregations_path: str | None = None):
        """Read the Home Region's Locations from the cache, fetching them from eBird when missing."""
        national_dir = os.path.join(cache_dir, LOCATION_DIR, home_region.national)
        subnational_dir = os.path.join(national_dir, home_region.subnational)
        return cls(
            home_region,
            cached(
                os.path.join(national_dir, "subnationals.json"),
                lambda: client.get_regions("subnational1", home_region.national),
            ),
            cached(
                os.path.join(subnational_dir, "regionals.json"),
                lambda: client.get_regions("subnational2", home_region.subnational),
            ),
            cached(
                os.path.join(subnational_dir, "hotspots.json"),
                lambda: client.get_hotspots(home_region.subnational),
            ),
            read_aggregations(aggregations_path),
        )

    def names(self, scope: RegionalScopes, query: str = "") -> list[str]:
        """Names of the scope's Locations containing the query, ignoring case; nearby has none."""
        return [name for name, _ in self.locations.get(scope, []) if contains(name, query)]

    def resolve(self, scope: RegionalScopes, name: str | None = None) -> list[str]:
        """Location ids the name stands for in the scope; no name means the Home Region at that scope."""
        if scope not in self.locations:
            raise ValueError(f"{scope} is not a scope of named Locations")
        if name is None:
            return [self.home_codes[scope]]
        matches = MATCH_POLICY[scope]
        return [
            location_id for candidate, ids in self.locations[scope] if matches(candidate, name) for location_id in ids
        ]


def contains(candidate: str, name: str) -> bool:
    return name.lower() in candidate.lower()


def equals(candidate: str, name: str) -> bool:
    return candidate == name


# How a typed name picks Locations: Regions by partial name, Hotspots and Aggregations only by their exact name.
MATCH_POLICY = {
    RegionalScopes.SUBNATIONAL: contains,
    RegionalScopes.REGIONAL: contains,
    RegionalScopes.HOTSPOT: equals,
}
