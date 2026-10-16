from dataclasses import dataclass


@dataclass(frozen=True)
class Call:
    method: str
    args: tuple
    back: object = None
    hotspot: object = None


class FakeEbirdClient:
    """In-memory stand-in for the eBird API client.

    Each keyword argument names a client method and gives its response: a value, or a callable
    receiving the call's arguments. Every call is recorded with the `back`/`hotspot` settings
    the client held at that moment.
    """

    def __init__(self, **responses):
        self.responses = responses
        self.calls: list[Call] = []
        self.back = None
        self.hotspot = None

    def _respond(self, method, *args):
        self.calls.append(Call(method, args, self.back, self.hotspot))
        response = self.responses.get(method, [])
        return response(*args) if callable(response) else response

    def get_regions(self, rtype, region):
        return self._respond("get_regions", rtype, region)

    def get_hotspots(self, region):
        return self._respond("get_hotspots", region)

    def get_ebird_taxonomy(self):
        return self._respond("get_ebird_taxonomy")

    def get_national_species(self, country):
        return self._respond("get_national_species", country)

    def get_observations(self, area):
        return self._respond("get_observations", area)

    def get_notable_observations(self, area):
        return self._respond("get_notable_observations", area)

    def get_species_observations(self, species, area):
        return self._respond("get_species_observations", species, area)

    def get_nearby_observations(self, lat, lng, dist=25):
        return self._respond("get_nearby_observations", lat, lng, dist)

    def get_nearby_notable(self, lat, lng, dist=25):
        return self._respond("get_nearby_notable", lat, lng, dist)

    def get_nearby_species(self, species, lat, lng, dist=25):
        return self._respond("get_nearby_species", species, lat, lng, dist)


def observation(com_name, obs_dt, loc_name="Parc de l'Île-Saint-Quentin", subnational2_name=None):
    """An eBird observation payload with the fields the CLI reads."""
    payload = {"comName": com_name, "obsDt": obs_dt, "locName": loc_name}
    if subnational2_name is not None:
        payload["subnational2Name"] = subnational2_name
    return payload
