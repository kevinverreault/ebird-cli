from ebird.api import Client
from ..domain import Observation


class ObservationService:
    DEFAULT_DAYS = 7

    def __init__(self, api_key, locale, lat, long):
        self.api_client = Client(api_key, locale)
        self.api_client.detail = 'full'
        self.lat = lat
        self.long = long

    def configure_client(self, back, hotspot=True):
        self.api_client.back = back
        self.api_client.hotspot = hotspot

    def get_nearby_notable_observations(self, back=DEFAULT_DAYS) -> list:
        self.configure_client(back)

        results = self.api_client.get_nearby_notable(self.lat, self.long, 50)

        return self.get_observations_from_notable(results)

    def get_notable_observations(self, location_id, back=DEFAULT_DAYS) -> list:
        self.configure_client(back)

        results = self.api_client.get_notable_observations(location_id)

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
        self.configure_client(back)

        observations = self.api_client.get_nearby_observations(self.lat, self.long, 50)

        return self.get_observations_from_recent(observations)

    def get_recent_observations(self, locations: [], back=DEFAULT_DAYS) -> list:
        self.configure_client(back)

        observations = list()
        for loc in locations:
            observations.extend(self.api_client.get_observations(loc))

        return self.get_observations_from_recent(observations)

    def get_observations_from_recent(self, observations):
        unique = dict()
        for obsJson in observations:
            obs = Observation(obsJson)
            if obs.name not in unique.keys() or unique[obs.name].observation_datetime < obs.observation_datetime:
                unique[obs.name] = obs

        return sorted(unique.values(), key=lambda x: x.observation_datetime)

    def set_range_in_days(self, days):
        return days

