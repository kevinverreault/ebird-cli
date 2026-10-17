import json
import shutil

import pytest
from conftest import FIXTURES
from fakes import FakeEbirdClient

from ebird_cli.domain.region import Region
from ebird_cli.domain.regional_scopes import RegionalScopes
from ebird_cli.services.location_catalogue import LocationCatalogue

SUBNATIONAL_NAMES = ["Alberta", "Colombie-Britannique", "Nouveau-Brunswick", "Nouvelle-Écosse", "Ontario", "Québec"]
HOTSPOT_NAMES = [
    "Dunes de Tadoussac",
    "Dunes de Tadoussac--Halte",
    "Parc de l'Île-Saint-Quentin",
    "Parc national de la Mauricie",
    "Technoparc--Étang Hertel",
]


def load_catalogue(tmp_path, client=None, aggregations=None) -> LocationCatalogue:
    cache_dir = tmp_path / "cache"
    shutil.copytree(FIXTURES / "cache", cache_dir, dirs_exist_ok=True)
    return LocationCatalogue.load(Region("CA-QC-MR"), client or FakeEbirdClient(), str(cache_dir), aggregations)


def test_names_without_query_lists_every_subnational_region(tmp_path):
    catalogue = load_catalogue(tmp_path)

    assert catalogue.names(RegionalScopes.SUBNATIONAL) == SUBNATIONAL_NAMES


def test_names_without_query_lists_every_regional_region_and_hotspot(tmp_path):
    catalogue = load_catalogue(tmp_path)

    assert catalogue.names(RegionalScopes.REGIONAL) == ["Côte-Nord", "Montérégie", "Montréal", "Mauricie"]
    assert catalogue.names(RegionalScopes.HOTSPOT) == HOTSPOT_NAMES


def test_names_with_query_keeps_names_containing_it_ignoring_case(tmp_path):
    catalogue = load_catalogue(tmp_path)

    assert catalogue.names(RegionalScopes.REGIONAL, "MONT") == ["Montérégie", "Montréal"]
    assert catalogue.names(RegionalScopes.HOTSPOT, "tadoussac") == ["Dunes de Tadoussac", "Dunes de Tadoussac--Halte"]


def test_names_with_query_matches_regex_characters_literally(tmp_path):
    catalogue = load_catalogue(tmp_path)

    assert catalogue.names(RegionalScopes.HOTSPOT, "Tadoussac (") == []
    assert catalogue.names(RegionalScopes.HOTSPOT, "--.") == []


def test_hotspot_names_include_aggregations_merged_from_every_object_in_the_file(tmp_path):
    catalogue = load_catalogue(tmp_path, aggregations=str(FIXTURES / "aggregations.json"))

    assert catalogue.names(RegionalScopes.HOTSPOT) == HOTSPOT_NAMES + ["Technoparc", "Trois-Rivières"]
    assert catalogue.names(RegionalScopes.HOTSPOT, "techno") == ["Technoparc--Étang Hertel", "Technoparc"]
    assert catalogue.names(RegionalScopes.REGIONAL, "trois") == []


def test_aggregations_path_expands_the_home_directory(tmp_path, monkeypatch):
    home = tmp_path / "home"
    (home / "ebird_data").mkdir(parents=True)
    (home / "ebird_data" / "aggregations.json").write_text(json.dumps([{"Chez moi": ["L9"]}]), encoding="utf-8")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))

    catalogue = load_catalogue(tmp_path, aggregations="~/ebird_data/aggregations.json")

    assert catalogue.names(RegionalScopes.HOTSPOT) == HOTSPOT_NAMES + ["Chez moi"]


def test_missing_aggregations_file_is_ignored(tmp_path):
    catalogue = load_catalogue(tmp_path, aggregations=str(tmp_path / "missing.json"))

    assert catalogue.names(RegionalScopes.HOTSPOT) == HOTSPOT_NAMES


def test_resolve_region_name_gives_its_code(tmp_path):
    catalogue = load_catalogue(tmp_path)

    assert catalogue.resolve(RegionalScopes.REGIONAL, "Montréal") == ["CA-QC-MO"]
    assert catalogue.resolve(RegionalScopes.SUBNATIONAL, "Québec") == ["CA-QC"]


def test_resolve_region_needs_the_exact_name(tmp_path):
    catalogue = load_catalogue(tmp_path)

    assert catalogue.resolve(RegionalScopes.REGIONAL, "mont") == []
    assert catalogue.resolve(RegionalScopes.REGIONAL, "montréal") == []
    assert catalogue.resolve(RegionalScopes.SUBNATIONAL, "Nouv") == []


def test_resolve_hotspot_needs_the_exact_name(tmp_path):
    catalogue = load_catalogue(tmp_path)

    assert catalogue.resolve(RegionalScopes.HOTSPOT, "Dunes de Tadoussac") == ["L1001"]
    assert catalogue.resolve(RegionalScopes.HOTSPOT, "Tadoussac") == []
    assert catalogue.resolve(RegionalScopes.HOTSPOT, "dunes de tadoussac") == []


def test_resolve_aggregation_gives_all_its_hotspots(tmp_path):
    catalogue = load_catalogue(tmp_path, aggregations=str(FIXTURES / "aggregations.json"))

    assert catalogue.resolve(RegionalScopes.HOTSPOT, "Technoparc") == ["L3001", "L3002"]


def test_resolve_name_of_both_a_hotspot_and_an_aggregation_gives_both(tmp_path):
    aggregations = tmp_path / "aggregations.json"
    aggregations.write_text(json.dumps([{"Dunes de Tadoussac": ["L1009"]}]), encoding="utf-8")

    catalogue = load_catalogue(tmp_path, aggregations=str(aggregations))

    assert catalogue.resolve(RegionalScopes.HOTSPOT, "Dunes de Tadoussac") == ["L1001", "L1009"]


@pytest.mark.parametrize(
    ("scope", "home"),
    [
        (RegionalScopes.SUBNATIONAL, "CA-QC"),
        (RegionalScopes.REGIONAL, "CA-QC-MR"),
        (RegionalScopes.HOTSPOT, "CA-QC-MR"),
    ],
)
def test_resolve_without_a_name_gives_the_home_region_for_the_scope(tmp_path, scope, home):
    catalogue = load_catalogue(tmp_path)

    assert catalogue.resolve(scope) == [home]


def test_nearby_has_no_names_and_cannot_be_resolved(tmp_path):
    catalogue = load_catalogue(tmp_path)

    assert catalogue.names(RegionalScopes.NEARBY) == []
    assert catalogue.names(RegionalScopes.NEARBY, "Mont") == []
    with pytest.raises(ValueError, match="nearby"):
        catalogue.resolve(RegionalScopes.NEARBY)


def fetching_client():
    return FakeEbirdClient(
        get_regions=lambda rtype, region: (
            [{"code": "CA-QC", "name": "Québec"}, {"code": "CA-ON", "name": "Ontario"}]
            if rtype == "subnational1"
            else [{"code": "CA-QC-MR", "name": "Mauricie"}]
        ),
        get_hotspots=[{"locId": "L2001", "locName": "Parc de l'Île-Saint-Quentin", "subnational2Code": "CA-QC-MR"}],
    )


def test_load_fetches_the_home_region_locations_from_ebird_when_nothing_is_cached(tmp_path):
    client = fetching_client()

    catalogue = LocationCatalogue.load(Region("CA-QC-MR"), client, str(tmp_path))

    assert [(call.method, call.args) for call in client.calls] == [
        ("get_regions", ("subnational1", "CA")),
        ("get_regions", ("subnational2", "CA-QC")),
        ("get_hotspots", ("CA-QC",)),
    ]
    assert catalogue.names(RegionalScopes.SUBNATIONAL) == ["Québec", "Ontario"]
    assert catalogue.resolve(RegionalScopes.REGIONAL, "Mauricie") == ["CA-QC-MR"]
    assert catalogue.resolve(RegionalScopes.HOTSPOT, "Parc de l'Île-Saint-Quentin") == ["L2001"]


def test_load_reuses_what_an_earlier_load_cached_without_calling_ebird(tmp_path):
    LocationCatalogue.load(Region("CA-QC-MR"), fetching_client(), str(tmp_path))
    client = fetching_client()

    catalogue = LocationCatalogue.load(Region("CA-QC-MR"), client, str(tmp_path))

    assert client.calls == []
    assert catalogue.names(RegionalScopes.HOTSPOT) == ["Parc de l'Île-Saint-Quentin"]


def test_load_fetches_only_the_hotspots_when_they_alone_are_missing_from_the_cache(tmp_path):
    LocationCatalogue.load(Region("CA-QC-MR"), fetching_client(), str(tmp_path))
    (tmp_path / "location" / "CA" / "CA-QC" / "hotspots.json").unlink()
    client = fetching_client()

    catalogue = LocationCatalogue.load(Region("CA-QC-MR"), client, str(tmp_path))

    assert [(call.method, call.args) for call in client.calls] == [("get_hotspots", ("CA-QC",))]
    assert catalogue.names(RegionalScopes.HOTSPOT) == ["Parc de l'Île-Saint-Quentin"]
