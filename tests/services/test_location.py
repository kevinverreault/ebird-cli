import json

from conftest import FIXTURES

HOTSPOT_NAMES = [
    "Dunes de Tadoussac",
    "Dunes de Tadoussac--Halte",
    "Parc de l'Île-Saint-Quentin",
    "Parc national de la Mauricie",
    "Technoparc--Étang Hertel",
]


def test_aggregations_from_every_object_in_the_file_are_merged(make_cli):
    cli = make_cli(aggregations=str(FIXTURES / "aggregations.json"))

    assert cli.location_service.get_hotspots() == HOTSPOT_NAMES + ["Technoparc", "Trois-Rivières"]
    assert sorted(cli.location_service.get_region_ids_by_scope("Trois-Rivières", "hotspot")) == ["L2001", "L2003"]


def test_aggregations_path_expands_the_home_directory(make_cli, tmp_path, monkeypatch):
    home = tmp_path / "home"
    (home / "ebird_data").mkdir(parents=True)
    (home / "ebird_data" / "aggregations.json").write_text(json.dumps([{"Chez moi": ["L9"]}]), encoding="utf-8")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))

    cli = make_cli(aggregations="~/ebird_data/aggregations.json")

    assert cli.location_service.get_hotspots() == HOTSPOT_NAMES + ["Chez moi"]


def test_missing_aggregations_file_is_ignored(make_cli, tmp_path):
    cli = make_cli(aggregations=str(tmp_path / "missing.json"))

    assert cli.location_service.get_hotspots() == HOTSPOT_NAMES
    assert cli.location_service.get_region_ids_by_scope("Technoparc", "hotspot") == []


def test_hotspot_name_matching_both_a_hotspot_and_an_aggregation_resolves_to_both(make_cli, tmp_path):
    aggregations = tmp_path / "aggregations.json"
    aggregations.write_text(json.dumps([{"Dunes de Tadoussac": ["L1009"]}]), encoding="utf-8")

    cli = make_cli(aggregations=str(aggregations))

    assert cli.location_service.get_region_ids_by_scope("Dunes de Tadoussac", "hotspot") == ["L1001", "L1009"]
