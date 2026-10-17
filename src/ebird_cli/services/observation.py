from ..domain import Observation
from .ebird_client import EbirdClient


class ObservationService:
    DEFAULT_DAYS = 7
    NEARBY_DISTANCE_KM = 50

    def __init__(self, api_key, locale, lat, long, api_client=None):
        self.api_client = api_client or EbirdClient(api_key, locale)
        self.lat = lat
        self.long = long

    def require_coordinates(self):
        if self.lat is None or self.long is None:
            raise ValueError("nearby needs coordinates: set --lat and --long, or EBIRDLAT and EBIRDLONG")

    def get_nearby_notable_observations(self, back=DEFAULT_DAYS) -> list:
        self.require_coordinates()

        results = self.api_client.get_nearby_notable(
            self.lat, self.long, self.NEARBY_DISTANCE_KM, back=back, hotspot=True
        )

        return self.get_observations_from_notable(results)

    def get_notable_observations(self, location_id, back=DEFAULT_DAYS) -> list:
        results = self.api_client.get_notable_observations(location_id, back=back, hotspot=True)

        return self.get_observations_from_notable(results)

    def get_observations_from_notable(self, results):
        notable_observations = list()
        keys = set()

        for result in results:
            obs = Observation(result)
            key = f"{obs.location}-{obs.name}"
            if key not in keys:
                keys.add(key)
                notable_observations.append(obs)

        return sorted(notable_observations, key=lambda x: x.observation_datetime)

    def get_nearby_recent_observations(self, back=DEFAULT_DAYS) -> list:
        self.require_coordinates()

        observations = self.api_client.get_nearby_observations(
            self.lat, self.long, self.NEARBY_DISTANCE_KM, back=back, hotspot=True
        )

        return self.get_observations_from_recent(observations)

    def get_recent_observations(self, locations: list, back=DEFAULT_DAYS) -> list:
        locs = list(dict.fromkeys(locations))
        observations = self.api_client.get_observations(locs, back=back, hotspot=True)

        return self.get_observations_from_recent(observations)

    def get_species_observations(self, locations: list, species_code: str, back=DEFAULT_DAYS) -> list:
        locs = list(dict.fromkeys(locations))
        observations = self.api_client.get_species_observations(species_code, locs, back=back, hotspot=True)

        return self.get_observations_from_species(observations)

    def get_nearby_species_observations(self, species_code: str, back=DEFAULT_DAYS) -> list:
        self.require_coordinates()

        observations = self.api_client.get_nearby_species(species_code, self.lat, self.long, back=back, hotspot=True)

        return self.get_observations_from_species(observations)

    def get_observations_from_species(self, observations) -> list:
        unique = dict()
        for obsJson in observations:
            obs = Observation(obsJson)
            if obs.location not in unique or unique[obs.location].observation_datetime < obs.observation_datetime:
                unique[obs.location] = obs

        return sorted(unique.values(), key=lambda x: x.observation_datetime)

    def get_observations_from_recent(self, observations):
        unique = dict()
        for obsJson in observations:
            obs = Observation(obsJson)
            if obs.name not in unique or unique[obs.name].observation_datetime < obs.observation_datetime:
                unique[obs.name] = obs

        return sorted(unique.values(), key=lambda x: x.observation_datetime)
