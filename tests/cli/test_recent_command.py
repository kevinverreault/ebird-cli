import pytest
from conftest import FIXTURES, LAT, LONG, table_rows
from fakes import Call, FakeEbirdClient, observation

from ebird_cli.cli.grammar import CommandLineError


def only_call(cli) -> Call:
    assert len(cli.client.calls) == 1
    return cli.client.calls[0]


def test_recent_nearby_requests_nearby_observations_at_configured_coordinates(cli):
    cli.run("recent nearby")

    assert cli.client.calls == [Call("get_nearby_observations", (LAT, LONG, 50), back="7", hotspot=True)]


@pytest.mark.parametrize(("lat", "long"), [(None, None), (LAT, None), (None, LONG)])
@pytest.mark.parametrize("line", ["recent nearby", "recent nearby -species Canard colvert", "notable nearby"])
def test_nearby_without_coordinates_is_refused_without_calling_ebird(make_cli, lat, long, line):
    cli = make_cli(lat=lat, long=long)

    with pytest.raises(ValueError, match="--lat and --long"):
        cli.run(line)

    assert cli.client.calls == []


def test_recent_regional_resolves_region_name_to_its_code(cli):
    cli.run("recent regional -region Montréal")

    assert cli.client.calls == [Call("get_observations", (["CA-QC-MO"],), back="7", hotspot=True)]


def test_recent_regional_with_partial_name_requests_no_location(cli):
    cli.run("recent regional -region mont")

    assert only_call(cli).args == ([],)


def test_recent_subnational_resolves_subnational_name_to_its_code(cli):
    cli.run("recent subnational -region Québec")

    assert only_call(cli) == Call("get_observations", (["CA-QC"],), back="7", hotspot=True)


def test_recent_subnational_with_partial_name_requests_no_location(cli):
    cli.run("recent subnational -region Nouv")

    assert only_call(cli).args == ([],)


def test_recent_hotspot_resolves_multi_word_hotspot_name_by_exact_match(cli):
    cli.run("recent hotspot -region Dunes de Tadoussac")

    assert only_call(cli) == Call("get_observations", (["L1001"],), back="7", hotspot=True)


def test_recent_hotspot_with_partial_name_requests_no_location(cli):
    cli.run("recent hotspot -region Tadoussac")

    assert only_call(cli).args == ([],)


def test_recent_hotspot_expands_an_aggregation_to_all_its_locations(make_cli):
    cli = make_cli(aggregations=str(FIXTURES / "aggregations.json"))

    cli.run("recent hotspot -region Technoparc")

    assert sorted(only_call(cli).args[0]) == ["L3001", "L3002"]


@pytest.mark.parametrize(
    ("scope", "default_region"),
    [("regional", "CA-QC-MR"), ("hotspot", "CA-QC-MR"), ("subnational", "CA-QC")],
)
def test_recent_without_region_uses_the_default_region_for_the_scope(cli, scope, default_region):
    cli.run(f"recent {scope}")

    assert only_call(cli) == Call("get_observations", ([default_region],), back="7", hotspot=True)


def test_recent_species_looks_up_the_species_code_and_requests_species_observations(cli):
    cli.run("recent regional -region Montréal -species Harfang des neiges")

    assert cli.client.calls == [Call("get_species_observations", ("snoowl1", ["CA-QC-MO"]), back="7", hotspot=True)]


def test_recent_species_accepts_flags_in_any_order(cli):
    cli.run("recent regional -species Harfang des neiges -region Côte-Nord -back 3")

    assert only_call(cli) == Call("get_species_observations", ("snoowl1", ["CA-QC-CN"]), back="3", hotspot=True)


def test_recent_species_without_region_uses_the_default_region(cli):
    cli.run("recent hotspot -species Merle d'Amérique")

    assert only_call(cli).args == ("amerob", ["CA-QC-MR"])


def test_recent_nearby_species_requests_nearby_species_observations(cli):
    cli.run("recent nearby -species Canard colvert")

    assert cli.client.calls == [Call("get_nearby_species", ("mallar3", LAT, LONG, 25), back="7", hotspot=True)]


@pytest.mark.parametrize("species", ["Hibou des marais", "harfang des neiges", "Harfang"])
def test_recent_with_unknown_species_prints_nothing_and_calls_nothing(cli, capsys, species):
    cli.run(f"recent nearby -species {species}")

    assert cli.client.calls == []
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize(("back", "expected"), [("1", "1"), ("14", "14"), ("30", "30")])
def test_recent_back_within_1_to_30_is_passed_to_ebird(cli, back, expected):
    cli.run(f"recent regional -back {back}")

    assert only_call(cli).back == expected


@pytest.mark.parametrize("back", ["0", "31", "-3", "trois"])
def test_recent_back_outside_1_to_30_is_refused_without_calling_ebird(cli, back):
    with pytest.raises(CommandLineError, match=rf"argument -back: invalid choice: '{back}' \(choose from 1 to 30\)"):
        cli.run(f"recent regional -back {back}")

    assert cli.client.calls == []


def test_recent_without_back_asks_for_7_days(cli):
    cli.run("recent regional")

    assert only_call(cli).back == "7"


def test_recent_keeps_only_the_latest_observation_per_species_oldest_first(make_cli, capsys):
    cli = make_cli(
        FakeEbirdClient(
            get_observations=[
                observation("Geai bleu", "2026-10-15 09:00", loc_name="Parc national de la Mauricie"),
                observation("Canard colvert", "2026-10-12", loc_name="Parc de l'Île-Saint-Quentin"),
                observation("Geai bleu", "2026-10-13 07:30", loc_name="Parc de l'Île-Saint-Quentin"),
                observation("Harfang des neiges", "2026-10-14 16:45", loc_name="Aéroport de Trois-Rivières"),
            ]
        )
    )

    cli.run("recent regional")

    assert table_rows(capsys.readouterr().out) == [
        ["2026-10-12", "Canard colvert", "Parc de l'Île-Saint-Quentin"],
        ["2026-10-14", "Harfang des neiges", "Aéroport de Trois-Rivières"],
        ["2026-10-15", "Geai bleu", "Parc national de la Mauricie"],
    ]


def test_recent_species_keeps_only_the_latest_observation_per_location_oldest_first(make_cli, capsys):
    cli = make_cli(
        FakeEbirdClient(
            get_species_observations=[
                observation("Harfang des neiges", "2026-10-15 08:00", loc_name="Aéroport de Trois-Rivières"),
                observation("Harfang des neiges", "2026-10-11", loc_name="Parc de l'Île-Saint-Quentin"),
                observation("Harfang des neiges", "2026-10-13 12:00", loc_name="Aéroport de Trois-Rivières"),
            ]
        )
    )

    cli.run("recent regional -species Harfang des neiges")

    assert table_rows(capsys.readouterr().out) == [
        ["2026-10-11", "Harfang des neiges", "Parc de l'Île-Saint-Quentin"],
        ["2026-10-15", "Harfang des neiges", "Aéroport de Trois-Rivières"],
    ]
