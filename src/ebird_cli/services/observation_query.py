from collections.abc import Callable, Hashable
from enum import StrEnum

from ..domain import Observation
from ..domain.regional_scopes import RegionalScopes
from .location_catalogue import LocationCatalogue

DEFAULT_DAYS = 7
NEARBY_DISTANCE_KM = 50
# Nearby species queries have always used the eBird client's default radius rather than NEARBY_DISTANCE_KM.
NEARBY_SPECIES_DISTANCE_KM = 25


class ObservationKind(StrEnum):
    RECENT = "recent"
    NOTABLE = "notable"


def latest_per(key: Callable[[Observation], Hashable], observations: list[Observation]) -> list[Observation]:
    """The latest observation for each key, oldest first."""
    latest = {}
    for obs in observations:
        if key(obs) not in latest or latest[key(obs)].observation_datetime < obs.observation_datetime:
            latest[key(obs)] = obs
    return sorted(latest.values(), key=lambda x: x.observation_datetime)


def first_per(key: Callable[[Observation], Hashable], observations: list[Observation]) -> list[Observation]:
    """The first observation eBird returned for each key, oldest first."""
    first = {}
    for obs in observations:
        first.setdefault(key(obs), obs)
    return sorted(first.values(), key=lambda x: x.observation_datetime)


class ObservationQuery:
    """Observations of a kind at a Location or nearby, from whichever eBird request that takes."""

    def __init__(self, client, location_catalogue: LocationCatalogue, lat: str | None, long: str | None):
        self.client = client
        self.location_catalogue = location_catalogue
        self.lat = lat
        self.long = long

    def observations(
        self,
        kind: ObservationKind,
        scope: RegionalScopes,
        region: str | None = None,
        species_code: str | None = None,
        back=DEFAULT_DAYS,
    ) -> list[Observation]:
        """Region None means the Home Region at that scope; nearby ignores it and needs the user's coordinates."""
        if kind == ObservationKind.NOTABLE:
            if species_code is not None:
                raise ValueError("notable observations can't be narrowed to a species")
            return first_per(lambda obs: (obs.location, obs.name), self.notable(scope, region, back))
        if species_code is not None:
            return latest_per(lambda obs: obs.location, self.species(scope, region, species_code, back))
        return latest_per(lambda obs: obs.name, self.recent(scope, region, back))

    def recent(self, scope: RegionalScopes, region: str | None, back) -> list[Observation]:
        """Every species reported, as eBird returned them."""
        if scope == RegionalScopes.NEARBY:
            results = self.client.get_nearby_observations(
                *self.coordinates(), dist=NEARBY_DISTANCE_KM, back=back, hotspot=True
            )
        else:
            results = self.client.get_observations(self.location_ids(scope, region), back=back, hotspot=True)
        return [Observation(result) for result in results]

    def notable(self, scope: RegionalScopes, region: str | None, back) -> list[Observation]:
        """Notable species reported, as eBird returned them."""
        if scope == RegionalScopes.NEARBY:
            results = self.client.get_nearby_notable(
                *self.coordinates(), dist=NEARBY_DISTANCE_KM, back=back, hotspot=True
            )
        else:
            results = self.client.get_notable_observations(self.location_ids(scope, region), back=back, hotspot=True)
        return [Observation(result) for result in results]

    def species(self, scope: RegionalScopes, region: str | None, species_code: str, back) -> list[Observation]:
        """Reports of one species, as eBird returned them."""
        if scope == RegionalScopes.NEARBY:
            results = self.client.get_nearby_species(
                species_code, *self.coordinates(), dist=NEARBY_SPECIES_DISTANCE_KM, back=back, hotspot=True
            )
        else:
            results = self.client.get_species_observations(
                species_code, self.location_ids(scope, region), back=back, hotspot=True
            )
        return [Observation(result) for result in results]

    def coordinates(self) -> tuple[str, str]:
        """The user's coordinates, which every nearby query needs."""
        if self.lat is None or self.long is None:
            raise ValueError("nearby needs coordinates: set --lat and --long, or save them with settings")
        return self.lat, self.long

    def location_ids(self, scope: RegionalScopes, region: str | None) -> list[str]:
        """Location ids the region resolves to, each once."""
        return list(dict.fromkeys(self.location_catalogue.resolve(scope, region)))
