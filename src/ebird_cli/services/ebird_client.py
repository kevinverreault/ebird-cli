import requests
from ebird.api import Client, constants, observations


class EbirdClient(Client):
    """The ebird-api client plus the reference endpoints it doesn't wrap the way the CLI calls them.

    Client reads `back` and `hotspot` from its own attributes; the observation methods here take them
    per call instead, so callers never have to change the client's state before a request.
    """

    def __init__(self, api_key: str, locale: str):
        super().__init__(api_key, locale)
        self.detail = "full"
        # Client.locale holds the validated form; the taxonomy endpoint has always been sent the locale as given.
        self.taxonomy_locale = locale

    def get_observations(self, area, back=constants.DEFAULT_BACK, hotspot=False):
        return observations.get_observations(
            self.api_key,
            area,
            back=back,
            max_results=self.max_observations,
            locale=self.locale,
            provisional=self.provisional,
            hotspot=hotspot,
            detail=self.detail,
            category=self.category,
        )

    def get_notable_observations(self, area, back=constants.DEFAULT_BACK, hotspot=False):
        return observations.get_notable_observations(
            self.api_key,
            area,
            back=back,
            max_results=self.max_observations,
            locale=self.locale,
            hotspot=hotspot,
            detail=self.detail,
        )

    def get_species_observations(self, species, area, back=constants.DEFAULT_BACK, hotspot=False):
        return observations.get_species_observations(
            self.api_key,
            species,
            area,
            back=back,
            max_results=self.max_observations,
            locale=self.locale,
            provisional=self.provisional,
            hotspot=hotspot,
            detail=self.detail,
            category=self.category,
        )

    def get_nearby_observations(self, lat, lng, dist=25, back=constants.DEFAULT_BACK, hotspot=False):
        return observations.get_nearby_observations(
            self.api_key,
            lat,
            lng,
            dist=dist,
            back=back,
            max_results=self.max_observations,
            locale=self.locale,
            provisional=self.provisional,
            hotspot=hotspot,
            category=self.category,
        )

    def get_nearby_notable(self, lat, lng, dist=25, back=constants.DEFAULT_BACK, hotspot=False):
        return observations.get_nearby_notable(
            self.api_key,
            lat,
            lng,
            dist=dist,
            back=back,
            max_results=self.max_observations,
            locale=self.locale,
            hotspot=hotspot,
            detail=self.detail,
        )

    def get_nearby_species(self, species, lat, lng, dist=25, back=constants.DEFAULT_BACK, hotspot=False):
        return observations.get_nearby_species(
            self.api_key,
            species,
            lat,
            lng,
            dist=dist,
            back=back,
            max_results=self.max_observations,
            locale=self.locale,
            provisional=self.provisional,
            hotspot=hotspot,
            category=self.category,
        )

    def get_ebird_taxonomy(self) -> list[dict]:
        url = "https://api.ebird.org/v2/ref/taxonomy/ebird"
        headers = {"X-eBirdApiToken": self.api_key}
        params = {"fmt": "json", "locale": self.taxonomy_locale}
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()

    def get_national_species(self, country: str) -> list[str]:
        url = f"https://api.ebird.org/v2/product/spplist/{country}"
        headers = {"X-eBirdApiToken": self.api_key}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
