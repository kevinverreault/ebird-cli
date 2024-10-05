from ebird.api import Client
from ..domain import Observation


class ObservationService:
    DEFAULT_DAYS = 7

    def __init__(self, api_key, locale):
        self.api_client = Client(api_key, locale)
        self.back = self.DEFAULT_DAYS

    def configure_client(self, back, hotspot=True):
        self.api_client.back = back
        self.api_client.hotspot = hotspot

    def get_notable_observations(self, location_id) -> list:
        self.configure_client(self.back)

        results = self.api_client.get_notable_observations(location_id)

        notable_observations = list()
        keys = set()

        for result in results:
            obs = Observation(result)
            key = f"{obs.location}-{obs.name}"
            if key not in keys:
                keys.add(key)
                notable_observations.append(obs)

        return sorted(notable_observations, key=lambda x: x.observation_datetime)

    def get_unique_recent_observations(self, locations: [], descending=False) -> list:
        self.configure_client(self.back)

        observations = list()
        for loc in locations:
            observations.extend(self.api_client.get_observations(loc))

        unique = dict()
        for obsJson in observations:
            obs = Observation(obsJson)
            if obs.name not in unique.keys() or unique[obs.name].observation_datetime < obs.observation_datetime:
                unique[obs.name] = obs

        return sorted(unique.values(), key=lambda x: x.observation_datetime, reverse=descending)

    def set_range_in_days(self, days):
        self.back = days

