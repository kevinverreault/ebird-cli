import csv

from fakes import FakeEbirdClient

from ebird_cli.domain.region import Region
from ebird_cli.services.cache import CacheService

TAXONOMY = [
    {"sciName": "Anas platyrhynchos", "comName": "Canard colvert", "speciesCode": "mallar3"},
    {"sciName": "Bubo scandiacus", "comName": "Harfang des neiges", "speciesCode": "snoowl1"},
    {"sciName": "Apteryx australis", "comName": "Kiwi austral", "speciesCode": "soikiw1"},
]


def fake_client():
    return FakeEbirdClient(
        get_ebird_taxonomy=TAXONOMY,
        get_national_species=["mallar3", "snoowl1"],
    )


def build_cache(client, cache_dir):
    return CacheService("api-key", "fr", Region("CA-QC-MR"), api_client=client, cache_dir=str(cache_dir))


def read_csv(path):
    with open(path, encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def test_fetches_and_writes_taxonomy_csvs_when_cache_is_empty(tmp_path):
    client = fake_client()

    build_cache(client, tmp_path)

    assert [(call.method, call.args) for call in client.calls] == [
        ("get_ebird_taxonomy", ()),
        ("get_national_species", ("CA",)),
    ]
    assert read_csv(tmp_path / "taxonomy" / "taxonomy.csv") == TAXONOMY


def test_reuses_cached_taxonomy_without_calling_ebird(tmp_path):
    build_cache(fake_client(), tmp_path)
    client = fake_client()

    build_cache(client, tmp_path)

    assert client.calls == []


def test_national_taxonomy_keeps_only_species_on_the_national_list(tmp_path):
    cache = build_cache(fake_client(), tmp_path)

    assert cache.taxonomy_cache.national["comName"].to_list() == ["Canard colvert", "Harfang des neiges"]
    assert [row["comName"] for row in read_csv(tmp_path / "taxonomy" / "CA" / "taxonomy.csv")] == [
        "Canard colvert",
        "Harfang des neiges",
    ]
