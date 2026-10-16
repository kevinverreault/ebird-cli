import requests
from ebird.api import Client


class EbirdClient(Client):
    """The ebird-api client plus the reference endpoints it doesn't wrap the way the CLI calls them."""

    def __init__(self, api_key: str, locale: str):
        super().__init__(api_key, locale)
        self.detail = "full"
        # Client.locale holds the validated form; the taxonomy endpoint has always been sent the locale as given.
        self.taxonomy_locale = locale

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
